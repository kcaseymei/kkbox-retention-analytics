# Metric definitions

One place for what every reported number means: its grain, population, denominator, and where it is computed. Evidence labels: *documented* (official description), *verified* (full-data result in this repository), *hypothesis*. Code and reports are linked so each number can be reproduced.

## 0. Conventions

| Term | Meaning |
|---|---|
| Target month M | The calendar month in which a subscription expires and whose renewal is judged |
| Cutoff T | The last day of the month before M; features use data dated on or before T |
| Row of the model tables | One user in one target month (a user appears in many months) |
| Rebuilt labels | Computed from the transactions with the rules of the official labeller (`src/churn_labels.py`); reliable for target months up to 2017-02 |
| Official labels | `train.csv` (February 2017) and `train_v2.csv` (March 2017), training label files; not the competition test set |
| Label rate | Share of churn labels in a *labeled population*; it is **not** a platform-wide churn rate |

See [churn_definition.md](churn_definition.md) for the label rules and the comparison of rebuilt and official labels.

## 1. Population metrics

| Metric | Definition | Denominator or grain | Where |
|---|---|---|---|
| Expiring users in M (rebuilt) | Distinct users whose **last** expiration at T (ordering of the official labeller) lies in M | Users with at least one transaction up to T | `churn_labels.rebuild_labels`; notebook 02 (879,537 for February 2017) |
| Users with any expiration in M | Distinct users with any transaction up to T whose expiration lies in M | Wider than the previous metric (993,531 for February 2017 in SQL) | `sql/analysis/02_expiring_users_by_month.sql` |
| Official population | Users in `train.csv` / `train_v2.csv` | 992,931 / 970,960; 88.57% / 88.79% are inside the rebuilt rule | notebook 02; `reports/model_results.md` |
| Users without history | Users with no transaction on or before T | Only occurs in the official March population (2,524) | `subscription_features.has_history` |

## 2. Label metrics

| Metric | Definition | Denominator | Caveat |
|---|---|---|---|
| Renewal gap (days) | Days from the effective expiration to the first non-cancellation transaction after T; a cancellation moves the effective expiration earlier | Users in the population with a later non-cancellation transaction | Negative for early renewals; missing if none |
| Churn label | 1 if the gap is 30 or more days or there is no later non-cancellation transaction; 0 otherwise | Population of M | Right-censored after 2017-03-31, so rebuilt labels stop at 2017-02 |
| Early renewal | Renewal dated before the expiration (negative gap) | Population of M | The official files seem to ignore early renewals (supported hypothesis) |
| Churn label rate | Churn labels / users in the population | The month's population | Rebuilt 3.95% (February 2017) against official 6.39%: different populations and definitions |
| Renewal-gap band | Share of non-cancellation expirations by gap: early, same day, 1-7, 8-14, 15-29, 30 or more days, none | 18.7 million expirations dated 2015-02 to 2017-01 | `sql/analysis/08_renewal_gap.sql`; shares are of expirations, not users |

The SQL churn rate of `sql/analysis/06_monthly_churn.sql` is a **simplified** version (non-cancellation transactions only, one pass); its levels differ slightly from the Python rebuild (February 2017: 4.45% against 3.95%) and are used for the shape over time only.

## 3. Descriptive subscription metrics (PostgreSQL)

| Metric | Definition | Denominator | Where |
|---|---|---|---|
| Plan mix | Share of transactions by plan length (30, over 30, 0, under 30 days) | Transactions of release v1 | `05_plan_mix.sql`; 87.97% 30-day |
| Auto-renew share | Transactions with auto-renew on / transactions | By plan group | `05_plan_mix.sql` |
| Cohort retention at month k | Users with an active subscription at the end of month C+k / users whose first non-cancellation transaction is in month C | Cohort size; active = a non-cancellation transaction with transaction date <= d <= expiration | `07_cohort_retention.sql`; can rise again when lapsed users return |
| Retention by first plan | The same, split by the plan length of the first transaction | Users of each plan group | `09_cohort_retention_by_plan.sql` |

"First transaction" is left-censored (the data starts on 2015-01-01), so a cohort can contain returning users.

## 4. Behavioral and subscription features

The 57 model features are defined one by one in [feature_dictionary.md](feature_dictionary.md): windows of 7, 14, 30, 60, and 90 days include the cutoff day; missing listening is flagged, not zero; invalid `total_secs` (outside 0 to 86,400 per day) is ignored and flagged. Lead time (`days_to_expiration`) is the number of days from T to the last expiration, reported in bands 1-7, 8-14, 15-21, and 22-31 days.

## 5. Evaluation metrics (`src/evaluation.py`)

| Metric | Definition | Reading |
|---|---|---|
| Capacity K | Share of the month's expiring users that can be contacted: 5%, 10%, 20% (the real capacity is unknown) | Names the size of the list |
| Precision at K | Churners in the top K% list / size of the list | Hit rate of the list |
| Recall at K | Churners in the list / all churners of the month | Share of churners reached; a random list reaches K% |
| Lift at K | Precision at K / churn label rate of the month | Random = 1 |
| AUC | Probability that a random churner scores above a random non-churner | Ranking over all users, not only the top |
| Brier score and calibration | Mean squared error of the probabilities; mean predicted against observed rate by decile | Whether probabilities can be read as risks |
| Ties | Broken at random with a fixed seed | A yes/no rule flagging more than K% picks a random subset |

Accuracy is not used: predicting that nobody churns is about 91% accurate. Predicted risk is not the likelihood of responding to an offer.

## 6. Denominators at a glance

| Number | Denominator |
|---|---|
| Churn label rate | Users of the labeled population of the month (not the platform) |
| Share of users without listening | Users of the target-month population |
| Renewal-gap shares | Expirations |
| Plan mix | Transactions |
| Cohort retention | Users in the first-transaction cohort |
| Recall at K | All churners of the evaluated month |

## 7. Reproduction

Audit figures: `notebooks/01_data_audit.ipynb`. Labels and cohorts: `notebooks/02_population_and_churn.ipynb`. SQL metrics: `sql/analysis/` and `reports/sql_analysis.md` (reconciled with the audit by `sql/quality/01_reconcile_postgres.sql`). Features and leakage checks: `notebooks/03_behavioral_features.ipynb`. Model metrics: `notebooks/04_model_evaluation.ipynb` and `reports/model_results.md`.
