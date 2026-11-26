"""Pure calculation functions for the AI Assistant ROI model. No Streamlit here.

Modelling choices (where the brief left room for interpretation):
- Month 0 holds only the one-off cost (rollout + training time). Adoption and
  benefit are zero in month 0, and no licence/admin cost is charged then.
- Months 1..N carry benefit and running cost. Adoption ramps linearly:
  month m has adoption = target * min(m / ramp_months, 1), so with a 3-month
  ramp month 1 is 1/3 of target and month 3 reaches target. ramp_months <= 0
  means full adoption from month 1.
- Licences are paid for every staff seat (cost = staff x licence + admin),
  regardless of adoption, as specified.
- ROI = net value / total cost, over month 0..N, as a fraction (1.0 = 100%).
- Payback month = first month whose cumulative net value is >= 0
  (None if that never happens within the horizon).
- Break-even hours = hours saved per active user per week at which the
  steady-state monthly benefit (full target adoption) equals the monthly
  running cost (licences + admin). The one-off cost and the ramp are ignored.
- 12-month payback hours = hours saved per active user per week at which the
  cumulative net value at the end of month 12 is exactly zero, i.e. the
  one-off cost is recovered within the year. Includes the ramp and month 0.
"""

from __future__ import annotations

import pandas as pd

from assumptions import DEFAULTS


def _with_defaults(inputs: dict | None) -> dict:
    merged = dict(DEFAULTS)
    if inputs:
        merged.update(inputs)
    return merged


def adoption_for_month(month: int, target: float, ramp_months: float) -> float:
    if month <= 0:
        return 0.0
    if ramp_months <= 0:
        return float(target)
    return float(target) * min(month / ramp_months, 1.0)


def one_off_cost(inputs: dict) -> float:
    i = _with_defaults(inputs)
    training = i["training_hours_per_person"] * i["hourly_cost_gbp"] * i["staff"]
    return float(i["rollout_one_off_gbp"] + training)


def monthly_running_cost(inputs: dict) -> float:
    i = _with_defaults(inputs)
    return float(i["staff"] * i["licence_per_seat_month_gbp"] + i["admin_per_month_gbp"])


def monthly_benefit(inputs: dict, adoption: float) -> float:
    i = _with_defaults(inputs)
    return float(
        i["staff"]
        * adoption
        * i["hours_saved_per_week"]
        * i["working_weeks"] / 12
        * i["hourly_cost_gbp"]
        * i["realisation"]
    )


def monthly_table(inputs: dict | None = None, months: int = 12) -> pd.DataFrame:
    """Month 0..months with adoption, benefit, cost, net and cumulative net value."""
    i = _with_defaults(inputs)
    rows = []
    running = monthly_running_cost(i)
    for m in range(0, months + 1):
        adoption = adoption_for_month(m, i["adoption"], i["ramp_months"])
        benefit = monthly_benefit(i, adoption)
        cost = one_off_cost(i) if m == 0 else running
        rows.append({"month": m, "adoption": adoption, "benefit": benefit, "cost": cost})
    df = pd.DataFrame(rows)
    df["net"] = df["benefit"] - df["cost"]
    df["cumulative_net_value"] = df["net"].cumsum()
    return df


def summary(inputs: dict | None = None, months: int = 12) -> dict:
    df = monthly_table(inputs, months)
    total_benefit = float(df["benefit"].sum())
    total_cost = float(df["cost"].sum())
    net_value = total_benefit - total_cost
    roi = net_value / total_cost if total_cost else float("nan")
    paid_back = df.loc[df["cumulative_net_value"] >= 0, "month"]
    payback_month = int(paid_back.iloc[0]) if not paid_back.empty else None
    return {
        "total_benefit": total_benefit,
        "total_cost": total_cost,
        "net_value": net_value,
        "roi": roi,
        "payback_month": payback_month,
    }


def breakeven_hours(inputs: dict | None = None) -> float:
    """Hours saved per active user per week at which steady-state monthly
    benefit equals monthly running cost.

    Steady state means adoption is at its target. Benefit is linear in hours:
        hours = (staff x licence + admin)
                / (staff x adoption x working_weeks/12 x hourly_cost x realisation)
    Returns inf if no amount of time saved can break even (e.g. zero adoption).
    """
    i = _with_defaults(inputs)
    benefit_per_hour = monthly_benefit(dict(i, hours_saved_per_week=1.0), i["adoption"])
    if benefit_per_hour <= 0:
        return float("inf")
    return monthly_running_cost(i) / benefit_per_hour


def payback_hours_12m(inputs: dict | None = None, months: int = 12) -> float:
    """Hours saved per active user per week needed to pay back within the horizon.

    That is, the hours at which cumulative net value at the end of the horizon
    (one-off cost in month 0, ramp included) is exactly zero. Benefit is linear
    in hours, so: hours = total_cost / (total benefit per 1 hour saved per week).
    Returns inf if no amount of time saved can pay back (e.g. zero adoption).
    """
    i = _with_defaults(inputs)
    s = summary(dict(i, hours_saved_per_week=1.0), months)
    if s["total_benefit"] <= 0:
        return float("inf")
    return s["total_cost"] / s["total_benefit"]
