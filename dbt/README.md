# dbt project: retention marts

Staging and mart models with data tests, built locally on DuckDB first (the Snowflake target is added in the last step of stage D). dbt only transforms: the heavy work (scanning the 410 million listening rows and building the 63-column feature tables) stays in `src/` (DuckDB, later PySpark); the marts here are built on the finished feature files.

## Run

From this directory, in the dbt environment (see `requirements.txt`):

```bash
dbt debug --profiles-dir .      # connection check
dbt run --profiles-dir .        # build the models (about 20 seconds)
dbt test --profiles-dir .       # 38 data tests
dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .   # documentation and lineage graph
```

Inputs: the Kaggle files in `../data/raw/` and the feature files in `../data/processed/features/` (written by `python -m src.build_features`). The database file `../data/processed/kkbox_dbt.duckdb` is git-ignored. Paths can be changed with `--vars '{raw_dir: ..., processed_dir: ...}'`. No credentials are stored in this directory.

## Models

| Layer | Model | Grain | Purpose |
|---|---|---|---|
| staging | `stg_members` | one row per member | Typed members file (values cast, not cleaned) |
| staging | `stg_official_labels` | one row per user and official label file | The two official training label files stacked |
| staging | `stg_transactions` | one row per transaction | Both releases stacked with a `release` column, no de-duplication |
| mart | `mart_user_month_features` | one row per user and target month | Label plus 57 features at the cutoff, lead-time band, split role (training, validation, test, external) |
| mart | `mart_monthly_churn` | one row per target month | Users, churners, churn label rate, rate by auto-renew status |
| mart | `mart_cohort_retention` | cohort month × first plan group × month offset | Retention of first-time subscribers (2016-01 to 2016-06 cohorts) |

## Tests

- **Keys and domains:** unique and not-null keys, `is_churn` in (0, 1), allowed values of flags and categories.
- **Relationships (severity: warn):** transactions and the feature mart to `stg_members`. About 12% of the transaction rows and 13% of the user-months have no member profile; the project keeps them (they are not dropped to force integrity), so these two tests warn by design.
- **Reconciliation with the audit:** source row counts (members 6,769,473; labels 992,931 and 970,960; transactions 21,547,746 and 1,431,009), churn counts in the official files (63,471 and 87,330), and the February 2017 population and churn label rate (879,537 and 3.95%).
- **Leakage controls:** the cutoff of every row is the last day of the month before the target month; "days since" counts, tenure, and registration age are never negative; one row per user and month.

## Status

36 tests pass and 2 warn (the relationship tests above) on the full data. The marts reproduce the earlier results: February 2017 churn label rate 3.95%, 21.39% for auto-renew off against 1.60% for on, and the retention by first plan (70.6% after one month for 30-day plans).
