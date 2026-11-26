"""AI Assistant ROI: Streamlit front end. Run with `streamlit run app.py`."""

import math

import streamlit as st

from assumptions import DEFAULTS, LABELS
from logic import breakeven_hours, hand_checks, monthly_table, payback_hours_12m, summary

st.set_page_config(page_title="AI Assistant ROI", layout="wide")
st.title("AI Assistant ROI")
st.caption("12-month view. All defaults are estimates: adjust them in the sidebar.")

# (widget, kwargs) per assumption. Sliders for bounded ratios/small ranges,
# number inputs for open-ended money and headcount values.
CONTROLS = {
    "staff": ("number", dict(min_value=1, step=10)),
    "adoption": ("slider", dict(min_value=0.0, max_value=1.0, step=0.05)),
    "ramp_months": ("slider", dict(min_value=0, max_value=12, step=1)),
    "hours_saved_per_week": ("slider", dict(min_value=0.0, max_value=10.0, step=0.1)),
    "hourly_cost_gbp": ("number", dict(min_value=0.0, step=1.0)),
    "realisation": ("slider", dict(min_value=0.0, max_value=1.0, step=0.05)),
    "working_weeks": ("slider", dict(min_value=1, max_value=52, step=1)),
    "licence_per_seat_month_gbp": ("number", dict(min_value=0.0, step=1.0)),
    "admin_per_month_gbp": ("number", dict(min_value=0.0, step=100.0)),
    "rollout_one_off_gbp": ("number", dict(min_value=0.0, step=1000.0)),
    "training_hours_per_person": ("slider", dict(min_value=0.0, max_value=20.0, step=0.5)),
}

inputs = {}
with st.sidebar:
    st.header("Assumptions (estimates)")
    for key, (kind, kwargs) in CONTROLS.items():
        default = DEFAULTS[key]
        # Keep widget value type consistent with its step type.
        value = type(kwargs["step"])(default)
        widget = st.slider if kind == "slider" else st.number_input
        inputs[key] = widget(LABELS[key], value=value, key=key, **kwargs)
    inputs["seats_for_active_only"] = st.toggle(
        LABELS["seats_for_active_only"],
        value=DEFAULTS["seats_for_active_only"],
        key="seats_for_active_only",
        help="On: licences are bought for staff x adoption each month (following the ramp). "
        "Off: every member of staff gets a seat.",
    )

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
