"""Two descriptive signal analyses on the monthly feature tables (`src/build_features.py`).

1. **Listening decline.** For users who listened in the 30 days before the earlier 30-day window, compare the
   listening days of the last 30 days before the cutoff with the 30 days before that. Groups: stopped (no
   listening day in the last 30), declined (a drop of more than 25%, but not to zero), stable (within 25%),
   increased (more than 25%). Users without prior listening are not comparable and are left out.
2. **Renewal mode.** Manual renewers (the last transaction has auto-renew off) against auto-renewers: share of
   users, share of the churners, and churn label rate.

Both use only features measured at the cutoff (the last day of the month before the target month), so the
"last 30 days" are 1 to 31 days before the expiration, not exactly the 30 days before it. Results are
descriptive associations, not causal effects. Run `python -m src.signal_analysis` to write the tables to
`reports/signal_analysis/`.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FEATURES = ROOT / 'data' / 'processed' / 'features'
OUT = ROOT / 'reports' / 'signal_analysis'
COLUMNS = ['target_month', 'label_source', 'is_churn', 'has_log_90', 'active_days_30', 'active_days_60',
           'last_auto_renew']
THRESHOLD = 0.25
DECLINE_GROUPS = ['stopped (0 days in the last 30)', 'declined (more than 25%)', 'stable (within 25%)',
                  'increased (more than 25%)']


def decline_group(active_30, active_60, has_log_90, threshold=THRESHOLD):
    """Listening-decline group per user; ``None`` when the user has no listening in the earlier 30-day window.

    ``prior`` = listening days in days 31 to 60 before the cutoff (``active_days_60 - active_days_30``).
    """
    active_30 = pd.Series(active_30, dtype='float64').reset_index(drop=True)
    active_60 = pd.Series(active_60, dtype='float64').reset_index(drop=True)
    has_log = pd.Series(has_log_90).fillna(False).astype(bool).reset_index(drop=True)
    prior = active_60 - active_30
    comparable = has_log & (prior > 0)
    change = (active_30 - prior) / prior
    group = pd.Series(np.select(
        [~comparable, active_30 == 0, change < -threshold, change > threshold],
        [None, DECLINE_GROUPS[0], DECLINE_GROUPS[1], DECLINE_GROUPS[3]], default=DECLINE_GROUPS[2]), dtype=object)
    group[~comparable] = None
    return group


def decline_table(frame):
    """Per target month: users in each decline group, churn label rate per group, and the risk ratio of the
    users who stopped or declined against the stable users."""
    frame = frame.assign(group=decline_group(frame['active_days_30'], frame['active_days_60'], frame['has_log_90']).values)
    comparable = frame[frame['group'].notna()]
    rows = []
    for (month, source), part in comparable.groupby(['target_month', 'label_source']):
        row = {'target_month': month, 'label_source': source, 'comparable_users': len(part)}
        for name in DECLINE_GROUPS:
            sel = part[part['group'] == name]
            row[f'share_{name}'] = 100 * len(sel) / len(part)
            row[f'churn_rate_{name}'] = 100 * sel['is_churn'].mean() if len(sel) else np.nan
        fell = part[part['group'].isin(DECLINE_GROUPS[:2])]
        stable = part[part['group'] == DECLINE_GROUPS[2]]
        row['churn_rate_fell_or_stopped'] = 100 * fell['is_churn'].mean() if len(fell) else np.nan
        row['risk_ratio_fell_or_stopped_vs_stable'] = (
            fell['is_churn'].mean() / stable['is_churn'].mean() if len(fell) and stable['is_churn'].mean() > 0 else np.nan)
        rows.append(row)
    return pd.DataFrame(rows)


def renewal_mode_table(frame):
    """Per target month: manual renewers (auto-renew off on the last transaction) and auto-renewers."""
    known = frame[frame['last_auto_renew'].notna()]
    rows = []
    for (month, source), part in known.groupby(['target_month', 'label_source']):
        manual = part['last_auto_renew'] == 0
        churn = part['is_churn']
        rows.append({
            'target_month': month, 'label_source': source, 'users': len(part),
            'manual_share_of_users': 100 * manual.mean(),
            'manual_share_of_churners': 100 * churn[manual].sum() / churn.sum() if churn.sum() else np.nan,
            'churn_rate_manual': 100 * churn[manual].mean(), 'churn_rate_auto': 100 * churn[~manual].mean(),
            'risk_ratio_manual_vs_auto': churn[manual].mean() / churn[~manual].mean() if churn[~manual].mean() > 0 else np.nan})
    return pd.DataFrame(rows)


def decline_by_renewal_mode(frame):
    """Churn label rate by decline group within manual renewers and within auto-renewers (pooled months), to
    see whether the decline signal survives once renewal mode is held fixed."""
    frame = frame.assign(group=decline_group(frame['active_days_30'], frame['active_days_60'], frame['has_log_90']).values)
    frame = frame[frame['group'].notna() & frame['last_auto_renew'].notna()].copy()
    frame['renewal_mode'] = np.where(frame['last_auto_renew'] == 0, 'manual (auto-renew off)', 'auto-renew on')
    table = frame.groupby(['renewal_mode', 'group']).agg(users=('is_churn', 'size'),
                                                         churn_rate=('is_churn', lambda s: 100 * s.mean())).reset_index()
    table['group'] = pd.Categorical(table['group'], DECLINE_GROUPS, ordered=True)
    return table.sort_values(['renewal_mode', 'group']).reset_index(drop=True)


def load_features(months=None, features_dir=FEATURES):
    files = sorted(Path(features_dir).glob('features_*.parquet'))
    if months:
        files = [f for f in files if f.stem.split('_')[1] in months]
    return pd.concat([pd.read_parquet(f, columns=COLUMNS) for f in files], ignore_index=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frame = load_features()
    decline_table(frame).round(3).to_csv(OUT / 'decline_by_month.csv', index=False)
    renewal_mode_table(frame).round(3).to_csv(OUT / 'renewal_mode_by_month.csv', index=False)
    test = frame[frame['target_month'].isin(['2017-01', '2017-02'])]
    decline_by_renewal_mode(test).round(3).to_csv(OUT / 'decline_by_renewal_mode_test_months.csv', index=False)
    print('written to', OUT)


if __name__ == '__main__':
    main()
