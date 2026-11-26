"""Default assumptions for the AI Assistant ROI model.

Every value here is an ESTIMATE, not a measured figure. Replace them with
your own data where you have it; the app lets you override each one.
"""

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
