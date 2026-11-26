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
}
