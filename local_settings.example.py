"""Machine-specific paths for the audit notebook.

Copy this file to `local_settings.py` (git-ignored) and edit the paths for your machine.
"""
from pathlib import Path

# Folder holding the text-typed Parquet copies `user_logs.parquet` and `user_logs_v2.parquet`
# (create them with `python src/csv_to_parquet.py <csv files> --out-dir <folder>`).
PARQUET_DIR = Path("/path/to/parquet")

# Folder where DuckDB may spill large intermediate results; needs tens of gigabytes free.
TEMP_DIR = Path("/path/to/duckdb_tmp")
