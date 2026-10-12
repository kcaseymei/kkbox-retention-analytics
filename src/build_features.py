"""Build the feature table, one Parquet file per target month (DuckDB).

Run from the repository root (machine paths come from the git-ignored `local_settings.py`):

    python -m src.build_features                 # target months 2015-07 to 2017-03, skips finished months
    python -m src.build_features --months 2017-02 --overwrite

One row = a user in a target month. Features use only data on or before the month's cutoff (the last day of
the previous month). Labels: rebuilt labels from `data/processed/rebuilt_monthly_labels.parquet` (written by
`notebooks/02_population_and_churn.ipynb`) for 2015-07 to 2017-02, and the official `train_v2.csv` labels for
2017-03 (`label_source` says which). Output: `data/processed/features/features_<month>.parquet` (git-ignored).
"""
import argparse
import time
from pathlib import Path

import duckdb
import pandas as pd

from src import audit_checks as ac
from src import behavior_features as bf
from src import churn_labels as cl
from src import subscription_features as sf

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / 'data' / 'raw'
CACHE = ROOT / 'data' / 'processed' / 'rebuilt_monthly_labels.parquet'
OUT_DIR = ROOT / 'data' / 'processed' / 'features'
REBUILT_MONTHS = [f'{y}-{m:02d}' for y, m in [(2015, m) for m in range(7, 13)] + [(2016, m) for m in range(1, 13)]
                  + [(2017, 1), (2017, 2)]]
OFFICIAL_MONTHS = ['2017-03']
TX_COLUMNS = ('msno, payment_method_id, payment_plan_days, plan_list_price, actual_amount_paid, '
              'is_auto_renew, transaction_date, membership_expire_date, is_cancel')


def connect(parquet_dir, temp_dir):
    con = duckdb.connect()
    con.execute("SET memory_limit='8GB'")
    con.execute(f"SET temp_directory='{temp_dir}'")
    ac.register_parquet(con, 'logs_v1', Path(parquet_dir) / 'user_logs.parquet')
    for name, filename in {'tx_v1': 'transactions.csv', 'tx_v2': 'transactions_v2.csv',
                           'members': 'members_v3.csv', 'train_v2': 'train_v2.csv'}.items():
        ac.register_csv(con, name, RAW_DIR / filename)
    con.execute(f'CREATE OR REPLACE VIEW tx_all AS SELECT {TX_COLUMNS} FROM tx_v1 '
                f'UNION ALL SELECT {TX_COLUMNS} FROM tx_v2')
    return con


def population(con, month):
    """Users and labels of a target month: columns ``msno``, ``is_churn``, ``label_source``."""
    if month in OFFICIAL_MONTHS:
        frame = con.sql('SELECT msno, is_churn::INT AS is_churn FROM train_v2').df()
        frame['label_source'] = 'official'
        return frame
    frame = pd.read_parquet(CACHE, columns=['target_month', 'msno', 'is_churn'])
    frame = frame[frame.target_month == month][['msno', 'is_churn']].copy()
    frame['label_source'] = 'rebuilt'
    return frame


def build_month(con, month):
    """Feature table of one target month as a DataFrame (listening, subscription, and profile features)."""
    cutoff = cl.month_window(month)['cutoff']
    pop = population(con, month)
    con.register('pop', pop[['msno']])
    listening = bf.listening_features(con, 'logs_v1', 'pop', cutoff)
    subscription = sf.subscription_features(con, 'tx_all', 'pop', cutoff)
    profile = sf.profile_features(con, 'members', 'pop', cutoff)
    table = (pop.merge(listening, on='msno').merge(subscription, on='msno').merge(profile, on='msno'))
    table.insert(1, 'target_month', month)
    table.insert(2, 'cutoff', cutoff)
    return table


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--months', nargs='*', default=REBUILT_MONTHS + OFFICIAL_MONTHS)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    from local_settings import PARQUET_DIR, TEMP_DIR   # machine-specific, git-ignored
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = connect(PARQUET_DIR, TEMP_DIR)
    for month in args.months:
        path = OUT_DIR / f'features_{month}.parquet'
        if path.exists() and not args.overwrite:
            print(f'{month}: exists, skipped', flush=True)
            continue
        start = time.time()
        table = build_month(con, month)
        table.to_parquet(path, index=False)
        print(f'{month}: {len(table):,} users, {table.shape[1]} columns, {time.time() - start:.0f} s', flush=True)


if __name__ == '__main__':
    main()
