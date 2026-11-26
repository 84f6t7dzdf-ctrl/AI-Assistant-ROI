"""AI Assistant ROI: Streamlit front end. Run with `streamlit run app.py`."""

import math

import altair as alt
import streamlit as st

import pandas as pd
from assumptions import CONTROLS, DEFAULTS, LABELS, PRESET_OVERRIDES, SOURCES, clean_value, preset
from logic import (
    breakeven_hours,
    hand_checks,
    monthly_table,
    payback_hours_12m,
    pilot_plan,
    sensitivity,
    summary,
)

st.set_page_config(page_title="AI Assistant ROI", layout="wide")
st.title("AI Assistant ROI")
st.caption("12-month view. All defaults are estimates: adjust them in the sidebar.")

TOGGLE = "seats_for_active_only"


def _widget_value(key, value):
    # Keep widget value type consistent with its step type (int vs float).
    return type(CONTROLS[key][1]["step"])(value)


def _set_all(values):
    """Write a full set of values into the widgets' session state (one source of truth)."""
    for key in CONTROLS:
        st.session_state[key] = _widget_value(key, values[key])
    # Force the Assumptions table to rebuild from the new values.
    st.session_state["table_version"] += 1


def _apply_preset():
    """Fill every control with the chosen preset's values. The seats toggle is left alone."""
    _set_all(preset(st.session_state["preset"]))


def _reset():
    """Back to Base case defaults, including the seats toggle."""
    st.session_state["preset"] = "Base case"
    st.session_state[TOGGLE] = DEFAULTS[TOGGLE]
    _set_all(DEFAULTS)


def _apply_table_edits():
    """Copy edits from the Assumptions table into the shared session state."""
    edits = st.session_state[f"assumptions_table_{st.session_state['table_version']}"]["edited_rows"]
    keys = list(CONTROLS)
    for row, change in edits.items():
        if change.get("Value") is not None:
            key = keys[int(row)]
            st.session_state[key] = clean_value(key, change["Value"])
    st.session_state["table_version"] += 1


# First run: start everything at the defaults.
for key in CONTROLS:
    st.session_state.setdefault(key, _widget_value(key, DEFAULTS[key]))
st.session_state.setdefault(TOGGLE, DEFAULTS[TOGGLE])
st.session_state.setdefault("table_version", 0)

inputs = {}
with st.sidebar:
    st.selectbox(
        "Preset",
        list(PRESET_OVERRIDES),
        key="preset",
        on_change=_apply_preset,
        help="Fills in the assumptions below. You can still adjust them afterwards.",
    )
    st.button("Reset to defaults", on_click=_reset)
    st.header("Assumptions (estimates)")
    for key, (kind, kwargs) in CONTROLS.items():
        widget = st.slider if kind == "slider" else st.number_input
        inputs[key] = widget(LABELS[key], key=key, **kwargs)
    inputs[TOGGLE] = st.toggle(
        LABELS[TOGGLE],
        key=TOGGLE,
        help="On: licences are bought for staff x adoption each month (following the ramp). "
        "Off: every member of staff gets a seat.",
    )

with st.expander("Assumptions"):
    st.caption(
        "Edit a value to recalculate. This table and the sidebar show the same numbers, "
        "so a change in one appears in the other. Values outside a control's range are clamped."
    )
    st.data_editor(
        pd.DataFrame(
            {
                "Assumption": [LABELS[k] for k in CONTROLS],
                "Value": [float(inputs[k]) for k in CONTROLS],
                "Default": [float(DEFAULTS[k]) for k in CONTROLS],
                "Source": [SOURCES[k] for k in CONTROLS],
            }
        ),
        key=f"assumptions_table_{st.session_state['table_version']}",
        on_change=_apply_table_edits,
        disabled=["Assumption", "Default", "Source"],
        hide_index=True,
        height=(len(CONTROLS) + 1) * 35 + 3,
        column_config={"Value": st.column_config.NumberColumn(format="%g")},
    )
    st.caption(f"{LABELS[TOGGLE]}: **{'on' if inputs[TOGGLE] else 'off'}**. {SOURCES[TOGGLE]}")
    st.button("Reset to defaults", key="reset_table", on_click=_reset)

table = monthly_table(inputs)
s = summary(inputs)
be = breakeven_hours(inputs)
pb = payback_hours_12m(inputs)

c1, c2, c3, c4, c5 = st.columns(5)
net = s["net_value"]
c1.metric("Net value (12 months)", f"{'-' if net < 0 else ''}£{abs(net):,.0f}")
c2.metric("ROI", "n/a" if math.isnan(s["roi"]) else f"{s['roi']:.0%}")
c3.metric("Payback month", "Not within 12 months" if s["payback_month"] is None else f"Month {s['payback_month']}")
c4.metric("Break-even hours", "n/a" if math.isinf(be) else f"{be:.2f}")
c4.caption("hours per user per week to break even")
c5.metric("12-month payback hours", "n/a" if math.isinf(pb) else f"{pb:.2f}")
c5.caption("hours per user per week to pay back within 12 months")

st.subheader("Cumulative net value (£)")
st.line_chart(table.set_index("month")["cumulative_net_value"])

st.subheader("Sensitivity: 12-month net value (£)")
st.caption(
    "Each bar varies one assumption from its low to high value, with everything else "
    "as set in the sidebar. The line is the current net value. Widest range at the top."
)
sens = sensitivity(inputs)
sens["from"] = sens[["net_at_low", "net_at_high"]].min(axis=1)
sens["to"] = sens[["net_at_low", "net_at_high"]].max(axis=1)
sens["label"] = sens.apply(lambda r: f"{r['driver']} ({r['low']:g} to {r['high']:g})", axis=1)
order = sens["label"].tolist()
bars = alt.Chart(sens).mark_bar().encode(
    y=alt.Y("label:N", sort=order, title=None, axis=alt.Axis(labelLimit=320)),
    x=alt.X("from:Q", title="Net value (£)", axis=alt.Axis(format=",.0f")),
    x2="to:Q",
    tooltip=[
        alt.Tooltip("driver:N", title="Assumption"),
        alt.Tooltip("low:Q", title="Low value"),
        alt.Tooltip("net_at_low:Q", title="Net value at low", format=",.0f"),
        alt.Tooltip("high:Q", title="High value"),
        alt.Tooltip("net_at_high:Q", title="Net value at high", format=",.0f"),
    ],
)
base_line = alt.Chart(sens.head(1)).mark_rule(strokeDash=[4, 4]).encode(x="base_net_value:Q")
st.altair_chart((bars + base_line).properties(height=260))

st.subheader("Pilot plan")
st.markdown(pilot_plan(inputs))

with st.expander("Monthly table"):
    st.dataframe(table.style.format({
        "adoption": "{:.0%}", "benefit": "£{:,.0f}", "cost": "£{:,.0f}",
        "net": "£{:,.0f}", "cumulative_net_value": "£{:,.0f}",
    }), hide_index=True)

def _fmt(v):
    if v is None:
        return "None"
    if isinstance(v, int):
        return str(v)
    return f"{v:,.2f}" if abs(v) >= 100 else f"{v:.4f}"


checks = hand_checks()
n_passed = sum(c["passed"] for c in checks)
with st.expander(f"Checks: {n_passed}/{len(checks)} passed"):
    st.caption(
        "Reruns the model on the default assumptions (not your sidebar values) "
        "and compares it with numbers worked out by hand."
    )
    st.dataframe(
        [
            {
                "": "✅" if c["passed"] else "❌",
                "Check": c["name"],
                "Expected": _fmt(c["expected"]),
                "Actual": _fmt(c["actual"]),
            }
            for c in checks
        ],
        hide_index=True,
    )

st.caption(
    "Month 0 holds the one-off cost (rollout + training time). ROI = net value / total cost. "
    "Break-even hours is the time saved per active user per week at which steady-state monthly "
    "benefit equals monthly licence and admin cost. 12-month payback hours is the time saved per active "
    "user per week needed to also recover the one-off cost, so cumulative net value is zero at month 12."
)
