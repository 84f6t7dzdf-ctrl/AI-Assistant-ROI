"""Default assumptions for the AI Assistant ROI model.

Every value here is an ESTIMATE, not a measured figure. Replace them with
your own data where you have it; the app lets you override each one.
"""

from __future__ import annotations

DEFAULTS = {
    "staff": 500,                        # estimate: people given a seat
    "adoption": 0.6,                     # estimate: target share of staff actively using it
    "ramp_months": 3,                    # estimate: months to reach target adoption
    "hours_saved_per_week": 2.5,         # estimate: hours saved per active user per week
    "hourly_cost_gbp": 45,               # estimate: loaded cost of one staff hour (GBP)
    "realisation": 0.5,                  # estimate: share of saved time turned into real value
    "working_weeks": 46,                 # estimate: working weeks per year
    "licence_per_seat_month_gbp": 25,    # estimate: licence cost per seat per month (GBP)
    "admin_per_month_gbp": 2000,         # estimate: ongoing admin/support per month (GBP)
    "rollout_one_off_gbp": 40000,        # estimate: one-off rollout cost (GBP)
    "training_hours_per_person": 2,      # estimate: one-off training hours per person
    "seats_for_active_only": False,      # policy choice: licence only active users (staff x adoption)
}

# Where each number comes from. All are ESTIMATES until replaced with your own data.
SOURCES = {
    "staff": "Estimate. Replace with the HR headcount in scope for the rollout.",
    "adoption": "Estimate. Share of seat holders using it weekly; check against pilot usage logs.",
    "ramp_months": "Estimate. Time to reach target adoption; check against pilot usage logs.",
    "hours_saved_per_week": "Estimate. Self-reported time saved per active user; check with the pilot survey (Q1).",
    "hourly_cost_gbp": "Estimate. Loaded cost of a staff hour (salary plus on-costs); confirm with Finance.",
    "realisation": "Estimate. Share of saved time that turns into useful work; check with the pilot survey (Q2).",
    "working_weeks": "Estimate. 52 weeks less leave and bank holidays; confirm with HR.",
    "licence_per_seat_month_gbp": "Estimate. Licence price per seat per month; confirm with the vendor quote.",
    "admin_per_month_gbp": "Estimate. Ongoing admin and support time; confirm with IT.",
    "rollout_one_off_gbp": "Estimate. One-off set-up, security review and comms; confirm with IT.",
    "training_hours_per_person": "Estimate. Training time per person, costed at the hourly rate.",
    "seats_for_active_only": "Policy choice, not an estimate. Set with the toggle in the sidebar.",
}

# Editable numeric assumptions: (widget kind, bounds/step). Used by the sidebar
# and the Assumptions table, and to clamp values typed into the table.
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


def clean_value(key: str, value) -> int | float:
    """Clamp a typed value to the control's bounds and match its type (int/float).

    Slider values are also snapped to the slider's step so the sidebar can show them.
    """
    kind, kw = CONTROLS[key]
    num_type = type(kw["step"])
    v = float(value)
    if kind == "slider":
        v = kw["min_value"] + round((v - kw["min_value"]) / kw["step"]) * kw["step"]
        v = round(v, 10)
    v = max(v, kw["min_value"])
    if "max_value" in kw:
        v = min(v, kw["max_value"])
    return num_type(round(v)) if num_type is int else num_type(v)


# Human-readable labels, used by the app sidebar.
LABELS = {
    "staff": "Staff (seats)",
    "adoption": "Target adoption",
    "ramp_months": "Ramp-up months",
    "hours_saved_per_week": "Hours saved per user per week",
    "hourly_cost_gbp": "Hourly staff cost (£)",
    "realisation": "Realisation rate",
    "working_weeks": "Working weeks per year",
    "licence_per_seat_month_gbp": "Licence per seat per month (£)",
    "admin_per_month_gbp": "Admin per month (£)",
    "rollout_one_off_gbp": "One-off rollout (£)",
    "training_hours_per_person": "Training hours per person",
    "seats_for_active_only": "Buy seats only for active users",
}

# Named scenarios for the app's preset dropdown. Each starts from DEFAULTS and
# overrides only the values listed (also estimates). The seats toggle is not
# part of any preset, so it stays as the user left it.
PRESET_OVERRIDES = {
    "Base case": {},
    "Low case": {"adoption": 0.3, "hours_saved_per_week": 1.0},
    "Pilot": {"staff": 50, "rollout_one_off_gbp": 5000, "admin_per_month_gbp": 0},
}


def preset(name: str) -> dict:
    """Full set of assumptions for a named preset."""
    return {**DEFAULTS, **PRESET_OVERRIDES[name]}
