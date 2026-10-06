#!/usr/bin/env bash
# Build the KKBox database from the raw CSV files. Run from the repository root.
# Connects as the project role `kkbox` to the database `kkbox`; the password is read from ~/.pgpass.
# Override the client with PSQL=/path/to/psql if it is not on the PATH.
set -euo pipefail
PSQL="${PSQL:-psql}"
run() { "$PSQL" -h localhost -U kkbox -d kkbox -w -v ON_ERROR_STOP=1 -f "$1"; }

run sql/postgres/01_schemas.sql
run sql/postgres/02_staging_tables.sql
run sql/postgres/03_load_staging.sql
run sql/postgres/04_analytics_tables.sql
echo "Build finished. Check it with: $PSQL -h localhost -U kkbox -d kkbox -f sql/quality/01_reconcile_postgres.sql"
