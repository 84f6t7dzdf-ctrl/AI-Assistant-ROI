"""AI Assistant ROI: Streamlit front end. Run with `streamlit run app.py`."""

import math

import streamlit as st

from assumptions import DEFAULTS, LABELS
from logic import breakeven_hours, monthly_table, summary

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

table = monthly_table(inputs)
s = summary(inputs)
be = breakeven_hours(inputs)

c1, c2, c3, c4 = st.columns(4)
net = s["net_value"]
c1.metric("Net value (12 months)", f"{'-' if net < 0 else ''}£{abs(net):,.0f}")
c2.metric("ROI", "n/a" if math.isnan(s["roi"]) else f"{s['roi']:.0%}")
c3.metric("Payback month", "Not within 12 months" if s["payback_month"] is None else f"Month {s['payback_month']}")
c4.metric("Break-even hours", "n/a" if math.isinf(be) else f"{be:.2f}")
c4.caption("hours per user per week to break even")

st.subheader("Cumulative net value (£)")
st.line_chart(table.set_index("month")["cumulative_net_value"])

with st.expander("Monthly table"):
    st.dataframe(table.style.format({
        "adoption": "{:.0%}", "benefit": "£{:,.0f}", "cost": "£{:,.0f}",
        "net": "£{:,.0f}", "cumulative_net_value": "£{:,.0f}",
    }), hide_index=True)

st.caption(
    "Month 0 holds the one-off cost (rollout + training time). ROI = net value / total cost. "
    "Break-even hours is the time saved per active user per week at which steady-state monthly "
    "benefit equals monthly licence and admin cost."
)
