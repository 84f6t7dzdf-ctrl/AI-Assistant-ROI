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
  Break-even hours = 259,000 / (711,562.5 / 2.5) = 259,000 / 284,625 = 0.909969...
"""

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assumptions import DEFAULTS  # noqa: E402
from logic import breakeven_hours, monthly_table, summary  # noqa: E402


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
    assert breakeven_hours(DEFAULTS) == pytest.approx(259000 / 284625)
    # At break-even hours, net value is zero.
    at_be = dict(DEFAULTS, hours_saved_per_week=breakeven_hours(DEFAULTS))
    assert summary(at_be)["net_value"] == pytest.approx(0.0, abs=1e-6)


def test_no_payback_and_no_ramp():
    # Tiny savings: never pays back.
    assert summary(dict(DEFAULTS, hours_saved_per_week=0.1))["payback_month"] is None
    # ramp_months=0: full adoption from month 1.
    df = monthly_table(dict(DEFAULTS, ramp_months=0))
    assert df["adoption"].iloc[1] == pytest.approx(0.6)


def test_zero_adoption_breakeven_is_infinite():
    assert math.isinf(breakeven_hours(dict(DEFAULTS, adoption=0.0)))
