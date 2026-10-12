# Model card: monthly churn risk list

Status: baseline and one stronger model evaluated on three held-out months (2026-10-12). Details and tables: [reports/model_results.md](../reports/model_results.md).

## Intended use

Rank the subscribers whose last subscription expires in the coming month by risk of not renewing within 30 days, so that a limited number of users (5%, 10%, or 20% of the month's expiring users) can be prioritized for a retention action. It is a portfolio analysis on a public competition dataset, not a production system.

## Not intended for

Deciding who *responds* to an offer (risk is not treatment effect), estimating platform-wide churn (the labeled users are a selected population), or any causal statement about why users leave.

## Data and population

- WSDM KKBox churn data (Kaggle), both releases; users whose last expiration at the cutoff lies in the target month (rebuilt with the official labeller rules), 2015-07 to 2017-02; the official `train_v2` file for 2017-03.
- One row per user and target month; features use data on or before the cutoff (the last day of the previous month).

## Features (57 used; the full list is in [feature_dictionary.md](feature_dictionary.md))

31 listening features (windows of 7 to 90 days: active days, plays, listening seconds, songs, completed share, trends, recency, flags), 20 subscription-history features (tenure, transaction and cancellation counts, last plan, price, auto-renew, days to expiration, plan changes), 6 profile features (city, registration channel, gender, age, registration age). Missing listening is flagged, not zero. `has_member_profile` is not used.

## Models and training

Logistic regression and gradient boosting (`HistGradientBoostingClassifier`, fixed settings, no tuning) trained on a random sample of 100,000 users per month; training months must have complete labels by the cutoff of the evaluated month (months up to M-2; January is excluded when predicting March). Baselines: one-feature rules, mainly "last transaction has auto-renew off".

## Performance (recall of churners reached at 10% capacity)

| Month | Gradient boosting | Rule: no auto-renew | Random |
|---|---|---|---|
| 2017-01 (rebuilt labels) | 71.9% | 52.5% | 10% |
| 2017-02 (rebuilt labels) | 68.1% | 54.2% | 10% |
| 2017-03 (official labels) | 44.9% | 45.9% | 10% |

## Honest assessment of usefulness

The model clearly beats a random list and, on the rebuilt labels, the best simple rule by about 14 to 19 points of recall at 10% capacity. On the official March labels the advantage over the auto-renew rule disappears at 10% capacity. A logistic regression performs about as well as gradient boosting on the rebuilt months. Listening features add little on top of the subscription record (about 1 point at 10%). Before any use, the early-renewer labeling and the March population mismatch need to be understood; an experiment would be required to know whether contacting the listed users retains anyone.

## Known limitations

- Three evaluation months; performance drifts (AUC 0.885, 0.865, 0.810).
- Rebuilt labels differ from official labels for early renewers (open question); 108,802 official March users fall outside the rebuilt population rule.
- Members file is a later snapshot (2017-11); profile columns add nothing in the ablation, so they are not relied on.
- The two transaction releases overlap on 7,249 (user, date) keys and are stacked without a de-duplication rule; effects on counts and averages for the affected users are not quantified.
- Payment method codes are used as categories without known meanings.
- Calibration is good on January and February and under-predicts in March.
