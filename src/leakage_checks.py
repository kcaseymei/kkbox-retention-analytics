"""Leakage checks for the feature tables (DuckDB and pandas).

A feature table is leak-free when every value could have been computed on the cutoff day. The checks:

1. **Cutoff invariance** (`check_cutoff_invariance`): compute the features on the full data and again on data
   truncated at the cutoff; any value that differs used information from after the cutoff.
2. **Too good to be true** (`single_feature_auc`): a single feature that separates churners almost perfectly
   (area under the ROC curve above ``AUC_ALERT``) suggests the label leaked into the feature.
3. **Time-ordered splits** (`check_purge`): training months must end at least two months before the
   validation month, because the label of month M is complete only about 30 days after M ends.
4. **One row per user and month** (`check_unique_rows`).
"""
import numpy as np
import pandas as pd

from src import behavior_features as bf
from src import subscription_features as sf

AUC_ALERT = 0.90


def compare_frames(full, truncated, key='msno', tolerance=1e-9):
    """Per column, the number of rows whose values differ between two feature tables (NaN equals NaN).

    Numbers are equal when they differ by at most ``tolerance`` relative to their size: sums of decimals
    can differ in the last digits when the summation order differs (about 1e-15 relative), which is not leakage.
    """
    a, b = full.set_index(key).sort_index(), truncated.set_index(key).sort_index()
    if not a.index.equals(b.index) or list(a.columns) != list(b.columns):
        raise ValueError('The two feature tables must have the same users and columns')
    rows = []
    for column in a.columns:
        x, y = a[column], b[column]
        both_missing = x.isna() & y.isna()
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y) \
                and not pd.api.types.is_bool_dtype(x):
            limit = tolerance * np.maximum(1.0, np.maximum(x.abs(), y.abs()))
            same = both_missing | ((x - y).abs() <= limit)
        else:
            same = both_missing | (x == y)
        rows.append({'feature': column, 'rows_differing': int((~same.fillna(False)).sum())})
    return pd.DataFrame(rows).set_index('feature')


def check_cutoff_invariance(con, logs_relation, tx_relation, users_relation, cutoff):
    """Features on the full relations against features on relations cut at ``cutoff``.

    Returns a table of differing rows per feature (all zeros when no feature uses data after the cutoff).
    Profile features are not covered: they read a later snapshot of the members file and apply the
    registration-date rule themselves (tested in `tests/test_subscription_features.py`).
    """
    bf._date(cutoff)
    con.execute(f"CREATE OR REPLACE TEMP VIEW _cut_logs AS SELECT * FROM {bf._quote(logs_relation)} "
                f"WHERE date <= '{cutoff}'")
    con.execute(f"CREATE OR REPLACE TEMP VIEW _cut_tx AS SELECT * FROM {bf._quote(tx_relation)} "
                f"WHERE transaction_date <= '{cutoff}'")
    parts = []
    for name, full, cut in (
            ('listening', bf.listening_features(con, logs_relation, users_relation, cutoff),
             bf.listening_features(con, '_cut_logs', users_relation, cutoff)),
            ('subscription', sf.subscription_features(con, tx_relation, users_relation, cutoff),
             sf.subscription_features(con, '_cut_tx', users_relation, cutoff))):
        diff = compare_frames(full, cut)
        diff.insert(0, 'group', name)
        parts.append(diff)
    return pd.concat(parts)


def single_feature_auc(frame, label='is_churn', features=None):
    """Area under the ROC curve of each numeric or boolean feature alone, oriented to be at least 0.5.

    Rows with a missing feature value are left out of that feature's AUC. Computed from ranks.
    """
    y_all = frame[label]
    features = features or [c for c in frame.columns
                            if c != label and (pd.api.types.is_numeric_dtype(frame[c])
                                               or pd.api.types.is_bool_dtype(frame[c]))]
    result = {}
    for column in features:
        mask = frame[column].notna()
        y, x = y_all[mask].astype(int), frame.loc[mask, column].astype(float)
        positives = int(y.sum())
        negatives = len(y) - positives
        if positives == 0 or negatives == 0 or x.nunique() < 2:
            continue
        ranks = x.rank(method='average')
        auc = (ranks[y == 1].sum() - positives * (positives + 1) / 2) / (positives * negatives)
        result[column] = max(auc, 1 - auc)
    return pd.Series(result, name='auc').sort_values(ascending=False)


def _month_index(month):
    year, number = (int(part) for part in month.split('-'))
    return year * 12 + number - 1


def check_purge(train_months, validation_month):
    """True when every training month is at least two months before the validation month."""
    return all(_month_index(m) <= _month_index(validation_month) - 2 for m in train_months)


def check_unique_rows(frame, keys=('msno', 'target_month')):
    """Number of duplicated (user, month) rows; 0 expected."""
    return int(frame.duplicated(list(keys)).sum())
