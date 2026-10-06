# Data audit — complete dataset (v1 and v2)

Date: 2026-10-05
Status: Audit executed on the full data; no cleaning has been applied. Open items are listed at the end.

## Scope and evidence labels

- **Source:** WSDM – KKBox's Churn Prediction Challenge (Kaggle), both releases: `train.csv`, `train_v2.csv`, `sample_submission_zero.csv`, `sample_submission_v2.csv`, `members_v3.csv`, `transactions.csv`, `transactions_v2.csv`, `user_logs.csv`, `user_logs_v2.csv`, plus `WSDMChurnLabeller.scala`. The official description is summarized in [source_dataset_notes.md](../docs/source_dataset_notes.md).
- **Evidence:** every figure below is a **full-data** result (every row of every file), reproduced by `notebooks/01_data_audit.ipynb` (section numbers in brackets). Statements marked *documented* come from the official description and are not verified locally; statements marked *hypothesis* are not verified.
- **Method:** DuckDB through the reusable checks in `src/audit_checks.py`; all columns are read as text and interpreted inside each check, so source values are never altered. The 30.5 GB `user_logs.csv` and `user_logs_v2.csv` were converted once to text-typed Parquet with a row-count check against the CSVs (392,106,543 and 18,396,362 rows).
- **Not done here:** no deletion, imputation, de-duplication, or type coercion of source data; no verification of the label windows from transactions; no reconstruction of labels.

## Release map (see notebook 1.3)

| Data | v1 | v2 | Relationship | Combination rule |
|---|---|---|---|---|
| Label tables | `train.csv`: 992,931 users, 6.39% churn labels (documented: February 2017 expirations) | `train_v2.csv`: 970,960 users, 8.99% (documented: March 2017) | 881,701 users in both; the label differs for 45,990 | Keep both as observations (user × window); no de-duplication |
| Test rosters | `sample_submission_zero.csv`: 970,960 users | `sample_submission_v2.csv`: 907,471 users (documented: April 2017, labels not public) | `sub_zero` has exactly the `train_v2` users | Not combined; placeholder predictions only |
| Members | `members_v3.csv`: 6,769,473 members (single release) | n/a | 88.34% of `train_v1` and 88.67% of `train_v2` users have a profile | Left join |
| Transactions | `transactions.csv`: 21,547,746 rows, 2015-01-01 to 2017-02-28 | `transactions_v2.csv`: 1,431,009 rows (1,069,822 in March 2017, 361,187 earlier) | No identical rows; 7,249 (user, date) keys occur in both | Stack as `tx_all`, keep every row |
| User logs | `user_logs.csv`: 392,106,543 rows, 2015-01-01 to 2017-02-28 | `user_logs_v2.csv`: 18,396,362 rows, 2017-03-01 to 2017-03-31 | No date in both releases | Stack as `logs_all` |

## Findings by table

**Label tables and test rosters [2].** `msno` is unique and complete in all four files and `is_churn` is binary; example predictions are all 0 (placeholders, not outcomes). Label rates are within each labeled population, not platform churn rates. Overlapping users change label between windows (0→0 824,659; 0→1 40,721; 1→0 5,269; 1→1 11,052). `sub_v2` has 88.32% of its users in `train_v2` and 88.26% in `train_v1`.

**Members [3].** 6,769,473 rows, unique and complete `msno`. Gender is missing for 4,429,505 members (65.43%). Age (`bd`) is 0 for 4,540,215 (67.07%), negative for 274, above 100 for 5,377, ranging from -7,168 to 2,016; only 2,223,607 (32.85%) lie within 1–100. Registration dates are valid (2004-03-26 to 2017-04-29); 154,166 members (2.28%) registered after 2017-02-28. One record has `registered_via = -1`. Profile coverage: `train_v1` 88.34%, `train_v2` and `sub_zero` 88.67%, `sub_v2` 87.62%; users without a profile have a lower label rate (`train_v2`: 5.35% against 9.46%), so an inner join would change the population.

**Transactions [4].** No missing values. v1 has 3,339 exact-duplicate rows, v2 none. The pair (`msno`, `transaction_date`) is not a key (286,404 excess rows in v1, 33,292 in v2). 153,660 v1 rows (6,460 non-cancellations) and 5,106 v2 rows (2 non-cancellations) expire before the transaction date; 9,840 v1 rows expire before 2015, 1,776 of them on 1970-01-01. v2 has 19,357 rows with an expiration more than 1,000 days after the transaction (largest 7,303 days, one member), v1 none. Zero-day plans: 870,124 rows in v1 (4.04%) and 2,218 in v2 (0.15%), almost all with a nonzero payment. `transactions_v2` is not March-only: besides the 1,069,822 March rows it holds 361,187 earlier rows that look like a supplement to v1 (*hypothesis*); the 7,249 shared keys look complementary rather than conflicting (*hypothesis*).

**User logs [5].** One row per user and day, unique within each release, with no date in both releases; 27 consecutive months; no missing, non-numeric, or invalid values; every `msno` has 44 characters. `total_secs` is negative in 61,493 v1 rows and above one day (86,400 seconds) in 142,993 v1 rows and 4,200 v2 rows, about 0.052% of v1 rows and 0.023% of v2 rows (breakdown in register item DQ-001). 998,583 users appear in both releases.

**Cross-table coverage [3.5, 5.6].** About 12–13% of labeled and test users have no log row and about 11–12% have no member profile; whether these are the same users is untested.

## Decisions taken

- Preserve all source values; flag, do not delete, anomalous rows (planned treatments in [data_quality_issues.md](data_quality_issues.md)).
- Stack releases only through views with a `release` column during the audit; physical merged tables are built in the staging step after the combination rules are settled.
- Do not de-duplicate label tables; derive user-level tables separately with a stated rule.
- Keep all labeled users with a left join to members; handle missing profiles and missing logs explicitly in features (absence is not zero listening).

## Open items

- Verify the label windows (February and March 2017) from transactions; define cutoffs and feature windows.
- Explain the 361,187 pre-March rows in `transactions_v2`, the 3,339 exact duplicates and the 1970-01-01 dates in v1, and decide how conflicting shared keys are handled when membership sequences are rebuilt.
- Set thresholds and the treatment for implausible `total_secs`.
- Training-user coverage in the transaction tables; overlap between users without logs and users without profiles.
- Confirm reproducibility with a restart-and-run-all of the notebook (the last saved run was sequential but not from a fresh kernel).

## Reproduce

Install `requirements.txt` (pandas and DuckDB). Open `notebooks/01_data_audit.ipynb` from the `notebooks/` directory; the setup cell holds the data paths (raw CSVs in `data/raw/`, user-log Parquet files on an external drive) and must be edited for another machine. Run all cells; the user-log sections scan about 410 million rows and take minutes. Tests: `python -m unittest tests.test_audit_checks tests.test_audit_display`.
