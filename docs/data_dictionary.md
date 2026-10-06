# Data dictionary — KKBox audit (v1 and v2)

Date: 2026-10-05

Observed schemas, grain, and ranges from the full-data audit in `notebooks/01_data_audit.ipynb` (section numbers in brackets). Definitions and units marked *documented* come from the official description ([source_dataset_notes.md](source_dataset_notes.md)) and are not verified locally. Issue identifiers (DQ-xxx) refer to [../reports/data_quality_issues.md](../reports/data_quality_issues.md). Source values are never altered; "proposed type" is how a later layer should parse the text stored in the raw files. Do not infer meanings of codes (`city`, `registered_via`, `payment_method_id`) from their numbers.

## Tables, grain, and release map

| Table (notebook name) | Source file | Rows | Verified grain | Key |
|---|---|---|---|---|
| `train_v1` | `train.csv` | 992,931 | One row per user in the February 2017 label window (*documented*) [2.2] | `msno` (unique, complete) |
| `train_v2` | `train_v2.csv` | 970,960 | One row per user in the March 2017 label window (*documented*) [2.2] | `msno` (unique, complete) |
| `sub_zero` | `sample_submission_zero.csv` | 970,960 | One placeholder prediction per user; same user set as `train_v2` [2.5] | `msno` |
| `sub_v2` | `sample_submission_v2.csv` | 907,471 | One placeholder prediction per user (April 2017 window, *documented*) [2.5] | `msno` |
| `members` | `members_v3.csv` | 6,769,473 | One row per member [3.1] | `msno` (unique, complete) |
| `tx_v1` | `transactions.csv` | 21,547,746 | One subscription or payment record; several per user, several per user and day [4.1] | None; (`msno`, `transaction_date`) is not unique |
| `tx_v2` | `transactions_v2.csv` | 1,431,009 | Same as above; 1,069,822 rows in March 2017 and 361,187 earlier [4.3] | None |
| `logs_v1` | `user_logs.csv` | 392,106,543 | One daily listening summary per user and day [5.1] | (`msno`, `date`) unique, complete |
| `logs_v2` | `user_logs_v2.csv` | 18,396,362 | Same as above; March 2017 only [5.2] | (`msno`, `date`) unique, complete |

Combined views (audit phase, no row removed): `train_all`, `tx_all`, `logs_all`, each with a `release` column. Combination rules and relationships: notebook section 1.3 and the audit report.

## Label tables and rosters (`train_v1`, `train_v2`, `sub_zero`, `sub_v2`)

| Field | Raw form | Proposed type | Definition | Observed | Notes |
|---|---|---|---|---|---|
| `msno` | text | string | Anonymized user identifier | No missing and no duplicates in any of the four files | Join key across all tables; identifier length and padding were checked only in the user logs |
| `is_churn` | text `0` / `1` | integer (0/1) | Training files: `1` = no new valid subscription within 30 days after the expiration date, `0` = renewal (*documented*; rule in `docs/churn_definition.md`). Rosters: placeholder predictions | `train_v1` 6.39% ones; `train_v2` 8.99% ones; rosters all 0 [2.3, 2.5] | Rates are within each labeled population, not platform churn rates (DQ-017) |

## Members (`members`)

| Field | Raw form | Proposed type | Definition | Observed | Notes |
|---|---|---|---|---|---|
| `msno` | text | string | User identifier | 6,769,473 unique, none missing | |
| `city` | text code | categorical (code) | City code (meaning unknown) | 21 distinct codes (1 to 22, no 2); code 1 holds 70.97%; none missing [3.4] | Do not infer meanings |
| `bd` | text integer | integer | Age (*documented*, with outliers) | -7,168 to 2,016; 0 for 67.07%; 274 negative; 5,377 above 100; 32.85% within 1–100 [3.2] | Zero looks like "unknown" but is unconfirmed (DQ-003) |
| `gender` | text | categorical | `male`, `female` | 65.43% missing [3.1] | Missing kept as "unknown" (DQ-002) |
| `registered_via` | text code | categorical (code) | Registration channel code (meaning unknown) | 18 distinct codes; 4 (41.26%), 3, 9, 7 dominate; one record with -1 [3.4] | DQ-005 |
| `registration_init_time` | `YYYYMMDD` | date | Registration date | No missing or invalid; 2004-03-26 to 2017-04-29; 154,166 after 2017-02-28 [3.3] | Apply a cutoff in features |

## Transactions (`tx_v1`, `tx_v2`)

| Field | Raw form | Proposed type | Definition | Observed (v1 / v2) | Notes |
|---|---|---|---|---|---|
| `msno` | text | string | User identifier | 2,363,626 / 1,197,050 users | |
| `payment_method_id` | text code | categorical (code) | Payment method code | 1–41 / 2–41; no missing | Codes are labels, not measures |
| `payment_plan_days` | text integer | integer | Plan length in days (*documented*) | 0–450 / 0–450; zero in 870,124 / 2,218 rows | Zero days is not zero payment (DQ-011) |
| `plan_list_price` | text integer | integer | List price in New Taiwan Dollar (*documented*) | 0–2,000 / 0–2,000 | |
| `actual_amount_paid` | text integer | integer | Amount paid in New Taiwan Dollar (*documented*) | 0–2,000 / 0–2,000 | Differs from list price in 7.96% / 0.83% of rows |
| `is_auto_renew` | text `0` / `1` | integer (0/1) | Auto-renewal flag | Only 0 and 1; 85.20% / 78.53% ones [4.2] | |
| `transaction_date` | `YYYYMMDD` | date | Transaction date | 2015-01-01 to 2017-02-28 / 2015-01-01 to 2017-03-31; none invalid [4.3] | |
| `membership_expire_date` | `YYYYMMDD` | date | Membership expiration date after the transaction | 1970-01-01 to 2017-03-31 / 2016-04-19 to 2036-10-15; none invalid [4.3] | Early, distant, and before-transaction values: DQ-008 to DQ-010 |
| `is_cancel` | text `0` / `1` | integer (0/1) | Whether the user cancelled the membership in this transaction (*documented*) | Only 0 and 1; 3.98% / 2.46% ones [4.2] | A cancellation is not churn |

## User logs (`logs_v1`, `logs_v2`)

| Field | Raw form | Proposed type | Definition | Observed (v1 / v2) | Notes |
|---|---|---|---|---|---|
| `msno` | text, 44 characters | string | User identifier | 5,234,111 / 1,103,894 users | No padding |
| `date` | `YYYYMMDD` | date | Listening day | 2015-01-01 to 2017-02-28 / 2017-03-01 to 2017-03-31; none invalid [5.2] | No date in both releases |
| `num_25` | text integer | integer | Songs played to less than 25% of their length (*documented*) | 0 to 18,798 / 0 to 5,639 | |
| `num_50` | text integer | integer | Songs played to 25–50% (*documented*) | 0 to 1,710 / 0 to 912 | |
| `num_75` | text integer | integer | Songs played to 50–75% (*documented*) | 0 to 1,690 / 0 to 508 | |
| `num_985` | text integer | integer | Songs played to 75–98.5% (*documented*) | 0 to 2,747 / 0 to 1,561 | |
| `num_100` | text integer | integer | Songs played to over 98.5% (*documented*) | 0 to 42,004 / 0 to 41,107 | Large maxima unconfirmed (DQ-015) |
| `num_unq` | text integer | integer | Number of unique songs played (*documented*) | 1 to 4,784 / 1 to 4,925 | Never zero |
| `total_secs` | text decimal | double | Total seconds played that day (*documented*) | -9.2e15 to 9.2e15 / 0.001 to 9,194,058.52 | Negative and above-one-day values: DQ-001 |

No field is missing in any table (blank or NULL) except `gender` in `members`. Retain identifiers as strings and parse dates explicitly; do not infer payment currency beyond the documented unit, listening units beyond the documented ones, churn rules from a column name, or timezone.
