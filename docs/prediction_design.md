# Prediction setup: cutoffs, feature windows, splits, and leakage controls

Status: **design, not implemented yet** (the feature tables and models are later stages). Facts quoted below are full-data results from `notebooks/01_data_audit.ipynb`, `notebooks/02_population_and_churn.ipynb`, or exploratory read-only checks (marked *exploratory*). Items marked *hypothesis* are not verified.

## 1. Unit of prediction and label

- **One row = a user in a target month** (a user can appear in many months). The population for a month is the users whose last expiration at the prediction time lies in that month (rule rebuilt in `src/churn_labels.py`).
- **Label:** churn (1) when no new valid subscription starts within 30 days of the effective expiration, renewal (0) otherwise (`docs/churn_definition.md`).
- **Label sources:** rebuilt labels for target months 2015-07 to 2017-02. The target months 2015-02 to 2015-06 (burn-in) are rebuilt and charted but **not used as training or evaluation rows**; their transactions and logs are still used as history for the features of later months. March 2017 exists only as the official `train_v2` file, because renewals after 2017-03-31 are invisible in the transactions.
- **Why a burn-in:** the data starts on 2015-01-01, so a 90-day lookback is fully available only from the target month 2015-05 (cutoff 2015-04-30), and early cohorts miss users on long plans until they renew. Starting at 2015-07 keeps two months of margin and avoids the unusual months around the 2015-04 spike. The start is a judgment; a sensitivity check (training from 2015-05 against 2015-07) is planned.

## 2. Prediction time

- **Cutoff T = the last day of the month before the target month** (for example 2017-01-31 for February 2017). The best agreement with the official labels was found at this cutoff.
- **Rule:** every feature uses data dated on or before T; the label uses events after T. Nothing dated after T may enter a feature.
- **Lead time** (days from T to the user's last expiration) is a feature and an evaluation dimension. Across the analysis months it is 1–7 days for 22.0% of users, 8–14 days for 22.0%, 15–21 days for 22.2%, and 22–31 days for 33.8% (*exploratory*). Users expiring early in the month leave little time to act, so results are reported by lead-time band.

## 3. Feature windows (looking back from T)

| Family | Source | Windows and examples | Evidence and cautions |
|---|---|---|---|
| Listening behavior | `user_logs` | Last 7, 14, 30, 60 and 90 days: active days, total seconds, plays by completion band, unique songs; trends (last 7 days against the previous 23, last 30 against the previous 30) | In the February 2017 cohort 68.8% have a log in the last 7 days, 77.1% in 30, and 80.5% in 90, so **19.5% have none in 90 days** (*exploratory*). Missing behavior gets an explicit flag and is **not** zero listening: users with no log in the last 30 days have a low churn label rate (2.76%), while among users with logs the rate falls as listening days rise (6.10% for 1–5 days, 3.80% for 16–25, 2.36% for 26–30; descriptive only) |
| Subscription history | `transactions` (both releases) | Tenure (days since the first transaction), number of transactions, latest plan days and price, auto-renew, cancellation history, plan changes, zero-price share, days to expiration at T | Histories are long: median 15 transactions, only 8.9% of the cohort have a first transaction under 90 days before T (*exploratory*), so 90-day windows are usually available |
| Profile | `members` | City and registration channel codes, age after cleaning with a flag, gender with "unknown" kept | `members_v3` is a later snapshot (2017-11) and 2.28% of members registered after 2017-02-28: use only attributes that do not change and a registration date on or before T. Do **not** use `has_member_profile` as a feature until it is shown to be knowable at T |
| Data quality | all | Implausible `total_secs` set to NULL with a validity flag, original kept | DQ-001 in `reports/data_quality_issues.md` |

## 4. Leakage controls

- Features use only data on or before T; outcome transactions, later cancellations, and later listening are used for the label only.
- The same user appears in many monthly cohorts, so a **random split would leak**; all splits are by time.
- **Purge rule:** the label of month M is complete only about 30 days after the end of M, so when predicting month M with cutoff T the training months must be **M-2 or earlier**.
- A label rebuilt for month M and the official label for March 2017 treat early renewers differently (open question), so March 2017 is reported separately as an external check.
- Cohorts with batch effects (for example 92,575 users expiring on 2015-04-30, 79.8% churn) are kept but reported with and without, and plan type is a feature.

## 5. Splits

| Role | Months | Note |
|---|---|---|
| Training and validation | 2015-07 to 2016-12 | Expanding window: for each validation month from 2016-07 on, train on months up to M-2 |
| Final test | 2017-01 and 2017-02 | Rebuilt labels; never used for tuning |
| External check | 2017-03 | Official `train_v2` labels, different treatment of early renewers; reported separately |

## 6. Evaluation

- Not accuracy: a list that predicts nobody churns scores about 91%.
- Precision, recall, and lift at capacity K = 5%, 10%, and 20% of each month's expiring users, against a random list and simple rules (for example "no auto-renew", "few listening days"), by month and by lead-time band; probability calibration.
- Predicted risk is not the likelihood of responding to an offer; the experiment design keeps them separate (README, "Business scenario").

## 7. Open questions

- How early renewers are labeled (affects labels and the March check).
- Whether to model all months together or to down-weight batch cohorts.
- Whether the strong signal of listening days holds across months (to be tested in the feature stage).
