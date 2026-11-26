"""Tests against hand-computed numbers using the default assumptions.

Hand working (defaults):
  Full-adoption monthly benefit = 500 x 0.6 x 2.5 x 46/12 x 45 x 0.5 = 64,687.50
  Month 1 adoption = 0.6 x 1/3 = 0.2 -> benefit 21,562.50
  Month 2 adoption = 0.4            -> benefit 43,125.00
  Months 3-12 adoption = 0.6        -> benefit 64,687.50 each
  Total benefit = 21,562.5 + 43,125 + 10 x 64,687.5 = 711,562.50
  Running cost  = 500 x 25 + 2,000 = 14,500 / month -> 174,000 over 12 months
  One-off (m0)  = 40,000 + 2 x 45 x 500 = 85,000
  Total cost    = 259,000
  Net value     = 452,562.50
  ROI           = 452,562.5 / 259,000 = 1.747345...
  Cumulative:   m0 -85,000; m1 -77,937.5; m2 -49,312.5; m3 +875 -> payback month 3
  Break-even hours (steady state) = monthly running cost / benefit per hour
                   = 14,500 / (500 x 0.6 x 46/12 x 45 x 0.5)
                   = 14,500 / 25,875 = 0.560386...
  12-month payback hours = total cost / (total benefit per 1 hour saved)
                   = 259,000 / (711,562.5 / 2.5) = 259,000 / 284,625 = 0.909969...
"""

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assumptions import DEFAULTS  # noqa: E402
from logic import breakeven_hours, hand_checks, monthly_table, payback_hours_12m, summary  # noqa: E402


def test_table_shape_and_columns():
    df = monthly_table(DEFAULTS)
    assert list(df["month"]) == list(range(13))
    for col in ["month", "adoption", "benefit", "cost", "cumulative_net_value"]:
        assert col in df.columns


def test_adoption_ramp():
    df = monthly_table(DEFAULTS)
    assert df["adoption"].tolist()[:5] == pytest.approx([0.0, 0.2, 0.4, 0.6, 0.6])
    assert df["adoption"].iloc[-1] == pytest.approx(0.6)


def test_monthly_benefit_and_cost():
    df = monthly_table(DEFAULTS)
    assert df["benefit"].tolist()[:4] == pytest.approx([0.0, 21562.5, 43125.0, 64687.5])
    assert df["cost"].iloc[0] == pytest.approx(85000.0)
    assert (df["cost"].iloc[1:] == 14500.0).all()


def test_cumulative_net_value():
    df = monthly_table(DEFAULTS)
    assert df["cumulative_net_value"].tolist()[:4] == pytest.approx(
        [-85000.0, -77937.5, -49312.5, 875.0]
    )
    assert df["cumulative_net_value"].iloc[-1] == pytest.approx(452562.5)


def test_summary():
    s = summary(DEFAULTS)
    assert s["total_benefit"] == pytest.approx(711562.5)
    assert s["total_cost"] == pytest.approx(259000.0)
    assert s["net_value"] == pytest.approx(452562.5)
    assert s["roi"] == pytest.approx(452562.5 / 259000)
    assert s["payback_month"] == 3


def test_breakeven_hours():
    assert breakeven_hours(DEFAULTS) == pytest.approx(14500 / 25875)
    assert breakeven_hours(DEFAULTS) == pytest.approx(0.560386, abs=1e-6)
    # At break-even hours, a steady-state month (month 12) nets to zero.
    at_be = dict(DEFAULTS, hours_saved_per_week=breakeven_hours(DEFAULTS))
    last = monthly_table(at_be).iloc[-1]
    assert last["benefit"] == pytest.approx(last["cost"])


def test_payback_hours_12m():
    assert payback_hours_12m(DEFAULTS) == pytest.approx(259000 / 284625)
    assert payback_hours_12m(DEFAULTS) == pytest.approx(0.909969, abs=1e-6)
    # At payback hours, cumulative net value at month 12 is zero.
    at_pb = dict(DEFAULTS, hours_saved_per_week=payback_hours_12m(DEFAULTS))
    assert monthly_table(at_pb)["cumulative_net_value"].iloc[-1] == pytest.approx(0.0, abs=1e-6)
    # Paying back the one-off cost needs more hours than steady-state break-even.
    assert payback_hours_12m(DEFAULTS) > breakeven_hours(DEFAULTS)
    assert math.isinf(payback_hours_12m(dict(DEFAULTS, adoption=0.0)))


def test_no_payback_and_no_ramp():
    # Tiny savings: never pays back.
    assert summary(dict(DEFAULTS, hours_saved_per_week=0.1))["payback_month"] is None
    # ramp_months=0: full adoption from month 1.
    df = monthly_table(dict(DEFAULTS, ramp_months=0))
    assert df["adoption"].iloc[1] == pytest.approx(0.6)


def test_zero_adoption_breakeven_is_infinite():
    assert math.isinf(breakeven_hours(dict(DEFAULTS, adoption=0.0)))


def test_one_full_month_matches_hand_check():
    # Month 3 is the first month at full target adoption.
    month = monthly_table(DEFAULTS).set_index("month").loc[3]
    assert month["benefit"] == pytest.approx(64687.5)  # 500 x 0.6 x 2.5 x 46/12 x 45 x 0.5
    assert month["cost"] == pytest.approx(14500.0)     # 500 x 25 + 2,000


def test_payback_month_is_none_when_benefit_below_cost():
    # 0.5 hours is below the 0.56 steady-state break-even, so every month's
    # benefit is below its cost and the running total never turns positive.
    inputs = dict(DEFAULTS, hours_saved_per_week=0.5)
    df = monthly_table(inputs)
    assert (df["benefit"] < df["cost"]).all()
    assert summary(inputs)["payback_month"] is None


def test_breakeven_hours_makes_benefit_equal_cost():
    at_be = dict(DEFAULTS, hours_saved_per_week=breakeven_hours(DEFAULTS))
    steady = monthly_table(at_be).query("month >= 3")
    assert steady["benefit"].tolist() == pytest.approx(steady["cost"].tolist())


def test_hand_checks_all_pass():
    checks = hand_checks()
    assert len(checks) == 9
    failed = [c["name"] for c in checks if not c["passed"]]
    assert failed == []
