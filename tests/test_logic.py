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

from assumptions import DEFAULTS, PRESET_OVERRIDES, preset  # noqa: E402
from logic import (  # noqa: E402
    breakeven_hours,
    hand_checks,
    monthly_table,
    payback_hours_12m,
    pilot_plan,
    sensitivity,
    summary,
)


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


def test_seats_for_active_only():
    """Hand working with the toggle on (other inputs at defaults):
    Seats follow adoption: m1 100, m2 200, m3-12 300.
    Running cost: m1 100x25+2,000 = 4,500; m2 200x25+2,000 = 7,000;
                  m3-12 300x25+2,000 = 9,500 each -> 4,500 + 7,000 + 10 x 9,500 = 106,500
    Total cost = 85,000 (one-off, unchanged) + 106,500 = 191,500
    Net value  = 711,562.5 - 191,500 = 520,062.5
    Cumulative: m0 -85,000; m1 -67,937.5; m2 -31,812.5; m3 +23,375 -> payback month 3
    Break-even hours (steady state) = 9,500 / 25,875 = 0.367150...
    12-month payback hours = 191,500 / 284,625 = 0.672815...
    """
    on = dict(DEFAULTS, seats_for_active_only=True)
    df = monthly_table(on)
    assert df["cost"].tolist()[:4] == pytest.approx([85000.0, 4500.0, 7000.0, 9500.0])
    assert df["cost"].iloc[-1] == pytest.approx(9500.0)
    assert df["cumulative_net_value"].tolist()[:4] == pytest.approx(
        [-85000.0, -67937.5, -31812.5, 23375.0]
    )
    s = summary(on)
    assert s["total_cost"] == pytest.approx(191500.0)
    assert s["net_value"] == pytest.approx(520062.5)
    assert s["payback_month"] == 3
    assert breakeven_hours(on) == pytest.approx(9500 / 25875)
    assert payback_hours_12m(on) == pytest.approx(191500 / 284625)
    # Default is off, so the original numbers are unchanged.
    assert DEFAULTS["seats_for_active_only"] is False
    assert summary(DEFAULTS)["total_cost"] == pytest.approx(259000.0)


def test_presets():
    """Hand working for the presets (everything not listed is a default).

    Base case = defaults: net value 452,562.5 (see top of file).
    Low case (adoption 0.3, hours 1.0):
      Full month benefit = 500 x 0.3 x 1.0 x 46/12 x 45 x 0.5 = 12,937.5
      Total benefit = 4,312.5 + 8,625 + 10 x 12,937.5 = 142,312.5
      Total cost unchanged = 259,000 -> net value -116,687.5, never pays back
    Pilot (staff 50, rollout 5,000, admin 0):
      One-off = 5,000 + 2 x 45 x 50 = 9,500; running = 50 x 25 = 1,250 / month
      Full month benefit = 50 x 0.6 x 2.5 x 46/12 x 45 x 0.5 = 6,468.75
      Total benefit = 2,156.25 + 4,312.5 + 10 x 6,468.75 = 71,156.25
      Total cost = 9,500 + 12 x 1,250 = 24,500 -> net value 46,656.25
      Cumulative: m0 -9,500; m1 -8,593.75; m2 -5,531.25; m3 -312.5; m4 +4,906.25
      -> payback month 4
    """
    assert list(PRESET_OVERRIDES) == ["Base case", "Low case", "Pilot"]
    assert preset("Base case") == DEFAULTS

    low = preset("Low case")
    assert (low["adoption"], low["hours_saved_per_week"]) == (0.3, 1.0)
    assert low["staff"] == DEFAULTS["staff"]
    s = summary(low)
    assert s["total_benefit"] == pytest.approx(142312.5)
    assert s["net_value"] == pytest.approx(-116687.5)
    assert s["payback_month"] is None

    pilot = preset("Pilot")
    assert (pilot["staff"], pilot["rollout_one_off_gbp"], pilot["admin_per_month_gbp"]) == (50, 5000, 0)
    s = summary(pilot)
    assert s["total_benefit"] == pytest.approx(71156.25)
    assert s["total_cost"] == pytest.approx(24500.0)
    assert s["net_value"] == pytest.approx(46656.25)
    assert s["payback_month"] == 4
    # Presets never touch the seats toggle.
    assert all("seats_for_active_only" not in o for o in PRESET_OVERRIDES.values())


def test_sensitivity():
    """Hand working at defaults. Base: benefit B = 711,562.5, cost C = 259,000, net 452,562.5.
    Benefit is proportional to hours, adoption, realisation and hourly cost.
      Hours 1.5 / 3.5:      B x 0.6 / 1.4 -> net 167,937.5 / 737,187.5   (range 569,250)
      Realisation 0.3/0.7:  B x 0.6 / 1.4 -> net 167,937.5 / 737,187.5   (range 569,250)
      Adoption 0.4 / 0.8:   B x 2/3 / 4/3 -> net 215,375 / 689,750       (range 474,375)
      Hourly cost 35 / 55:  B x 35/45, 55/45 = 553,437.5 / 869,687.5;
                            training 2 x 500 x rate moves C to 249,000 / 269,000
                            -> net 304,437.5 / 600,687.5                 (range 296,250)
      Licence 20 / 35:      C -/+ 12 x 500 x 5 or 10 = 229,000 / 319,000
                            -> net 482,562.5 / 392,562.5                 (range 90,000)
    """
    df = sensitivity(DEFAULTS).set_index("key")
    expected = {
        "hours_saved_per_week": (167937.5, 737187.5),
        "realisation": (167937.5, 737187.5),
        "adoption": (215375.0, 689750.0),
        "hourly_cost_gbp": (304437.5, 600687.5),
        "licence_per_seat_month_gbp": (482562.5, 392562.5),
    }
    for key, (lo, hi) in expected.items():
        assert df.loc[key, "net_at_low"] == pytest.approx(lo), key
        assert df.loc[key, "net_at_high"] == pytest.approx(hi), key
    assert df["base_net_value"].tolist() == pytest.approx([452562.5] * 5)

    ordered = sensitivity(DEFAULTS)
    assert ordered["range"].tolist() == pytest.approx([569250, 569250, 474375, 296250, 90000])
    assert ordered["key"].tolist()[2:] == ["adoption", "hourly_cost_gbp", "licence_per_seat_month_gbp"]


def test_pilot_plan():
    text = pilot_plan(DEFAULTS)
    assert "50 staff" in text
    assert "8 weeks" in text
    # Pass mark = steady-state break-even = 14,500 / 25,875 = 0.56
    assert "at least **0.56 hours per week**" in text
    assert "two-question survey" in text and "Usage logs" in text
    assert "realisation assumption, currently 50%" in text
    assert "currently 60% of staff active" in text
    # Pass mark follows the inputs: toggle on -> 9,500 / 25,875 = 0.37
    assert "**0.37 hours per week**" in pilot_plan(dict(DEFAULTS, seats_for_active_only=True))
    # Zero adoption: no amount of time saved breaks even.
    assert "not reachable" in pilot_plan(dict(DEFAULTS, adoption=0.0))
