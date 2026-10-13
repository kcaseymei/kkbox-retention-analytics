# Two retention signals: listening decline and renewal mode

Date: 2026-10-13. Reproduce: `python -m src.signal_analysis` (seconds; needs the feature tables from `python -m src.build_features`); the saved tables are in `reports/signal_analysis/`; tests: `tests/test_signal_analysis.py`.

**Evidence:** full-data results on every user of each target month, from the feature tables (features measured at the cutoff, the last day of the month before the expiry month). Rebuilt labels for 2015-07 to 2017-02; 2017-03 uses the official labels and is shown separately. These are descriptive associations, not causal effects, and no intervention effect is claimed.

## Definitions

- **Listening decline.** For users who listened in the earlier 30-day window (days 31 to 60 before the cutoff), compare the listening days of the last 30 days before the cutoff with that earlier window: **stopped** (0 listening days in the last 30), **declined** (a drop of more than 25%, not to zero), **stable** (within 25%), **increased** (more than 25%). Users with no listening in the earlier window are not comparable and are left out (20.1% to 29.9% of each month's population). "Fell or stopped" combines the first two groups. Because the cutoff is the month start, the last 30 days end 1 to 31 days **before the expiration**, not exactly on the 30 days before it.
- **Renewal mode.** **Manual renewers** are users whose last transaction before the cutoff has auto-renew off; the others are auto-renewers.
- **Risk ratio** = churn label rate of one group divided by that of the reference group.

## 1. Users whose listening fell churn more, but by about 1.5 times, not more

Churn label rate of users who fell or stopped listening against stable users:

| Month | Comparable users | Fell or stopped (share) | Churn rate: fell or stopped | Churn rate: stable | Ratio |
|---|---|---|---|---|---|
| 2016-07 | 557,896 | 20.5% | 5.03% | 3.27% | 1.54 |
| 2016-08 | 584,312 | 22.7% | 4.72% | 2.94% | 1.60 |
| 2016-09 | 605,845 | 22.2% | 4.50% | 3.65% | 1.23 |
| 2016-10 | 616,971 | 21.3% | 4.39% | 2.86% | 1.54 |
| 2016-11 | 626,239 | 20.3% | 6.92% | 3.11% | 2.23 |
| 2016-12 | 632,059 | 20.9% | 6.15% | 4.23% | 1.45 |
| 2017-01 | 631,972 | 19.3% | 4.85% | 2.74% | 1.77 |
| 2017-02 | 649,053 | 21.3% | 4.67% | 2.81% | 1.66 |
| 2017-03 (official labels) | 731,639 | 23.3% | 9.30% | 8.74% | 1.06 |

- Across all 21 target months the ratio has a **median of 1.48 and ranges from 0.99 to 2.23**; 18.9% to 23.3% of the comparable users fell or stopped. The two weakest months are the batch-cohort spike of 2016-03 (0.99) and the official March 2017 file (1.06), where churn is dominated by other effects or defined differently.
- **The signal survives when renewal mode is held fixed** (pooled January and February 2017):

| Renewal mode | Group | Users | Churn rate |
|---|---|---|---|
| Auto-renew on | Stopped | 37,808 | 2.78% |
| | Declined | 195,529 | 1.92% |
| | Stable | 626,552 | 1.11% |
| | Increased | 237,163 | 1.38% |
| Manual | Stopped | 665 | 72.63% |
| | Declined | 26,210 | 27.03% |
| | Stable | 117,098 | 11.69% |
| | Increased | 40,000 | 21.34% |

  Within each mode, users whose listening declined churn about 1.7 times (auto-renew) and 2.3 times (manual) as often as stable users. Two cautions: the group that **increased** its listening also churns more than the stable group (1.38% against 1.11% and 21.34% against 11.69%), so the signal is partly "listening changed" rather than "listening fell", and a percentage change is noisy for users with little prior listening (two days falling to one is -50%). The "stopped" group is small (665 manual users), so its 72.63% rate is imprecise.

## 2. Manual renewers are few but account for most of the churn

| Month | Users | Manual renewers (share of users) | Their share of the churners | Churn rate: manual | Churn rate: auto-renew | Ratio |
|---|---|---|---|---|---|---|
| 2016-07 | 766,155 | 14.8% | 70.8% | 26.5% | 1.90% | 14.0 |
| 2016-08 | 798,862 | 13.5% | 67.2% | 21.3% | 1.62% | 13.1 |
| 2016-09 | 844,477 | 15.0% | 80.2% | 33.7% | 1.47% | 22.9 |
| 2016-10 | 834,820 | 12.9% | 66.9% | 19.8% | 1.45% | 13.6 |
| 2016-11 | 890,486 | 17.6% | 87.5% | 45.2% | 1.38% | 32.8 |
| 2016-12 | 880,724 | 15.0% | 63.3% | 34.3% | 3.50% | 9.8 |
| 2017-01 | 867,529 | 13.4% | 69.9% | 23.5% | 1.56% | 15.0 |
| 2017-02 | 879,537 | 11.9% | 64.3% | 21.4% | 1.60% | 13.3 |
| 2017-03 (official labels) | 968,436 | 11.8% | 55.0% | 41.4% | 4.53% | 9.1 |

- From 2016-07 to 2017-02, manual renewers are **11.9% to 17.6% of the users and 63.3% to 87.5% of the churners**; the 87.5% is a single month (2016-11), the other months are 63% to 80%.
- **The pattern changed over time.** In 2015-07 to 2016-06 manual renewers were 13.5% to 16.7% of the users but only 30.5% to 57.5% of the churners (risk ratio 2.2 to 8.2): the churn rate of auto-renewers fell from 3% to 15% in 2015 and early 2016 to about 1.4% to 1.9% from mid-2016 on, while manual renewers stayed at about 20% to 45%. Any statement about "how much of the churn manual renewers account for" must name the period.
- Auto-renew status is the strongest single feature in the models (see `reports/model_results.md`); this table shows its size in each month. The official March 2017 file shows a weaker concentration (55.0%).

## What this suggests (hypotheses to test, not results)

- **Manual renewers** are the natural group for a reminder before the expiration date and for a prompt to turn on auto-renew; whether either action retains anyone needs a randomized experiment (Stage F).
- **A listening change** is a weaker, additional signal; its value on top of the subscription record is small in the models (about 1 point of recall at 10% capacity).

## Limits

- Associations on one dataset from 2017; the groups differ in many ways besides the signal (plan, tenure, payment method), and no adjustment beyond the renewal-mode split is made here.
- Auto-renew status is the flag of the last transaction before the cutoff; users can change it between the cutoff and the expiration.
- The official labels (March 2017) and the rebuilt labels define churn differently for early renewers (see `docs/churn_definition.md`), so the March row is not comparable with the others.
- The question of how early the signals appear is not answered here: the windows end at the cutoff, 1 to 31 days before the expiration (a lead-time experiment is a stretch goal, `docs/lead_time_experiment_design.md`).
