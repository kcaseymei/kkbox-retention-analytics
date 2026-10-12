"""Which feature families matter? Gradient boosting trained on subsets of the features (run from the repository root).

    python -m src.run_ablation               # about 10 minutes; writes reports/model_results/ablation.csv

Same protocol as `src/run_experiments.py` (purge rule, user sample per month, fixed settings) on the test months
2017-01 and 2017-02 and the external month 2017-03. Families: listening (from the user logs), subscription
(from the transactions), profile (from the members snapshot).
"""
import time

import pandas as pd

from src import evaluation as ev
from src import modeling as md
from src.run_experiments import OUT, PER_MONTH, training_months

LISTENING_PREFIXES = ('active_days_', 'plays_', 'secs_', 'unique_songs_', 'completed_share_', 'trend_days_')
LISTENING_NAMES = ('days_since_last_log', 'has_log_90', 'no_log_90_flag', 'has_invalid_secs_90')
MONTHS = ['2017-01', '2017-02', '2017-03']


def families(columns):
    listening = [c for c in columns if c.startswith(LISTENING_PREFIXES) or c in LISTENING_NAMES]
    profile = [c for c in md.PROFILE_COLUMNS if c in columns]
    subscription = [c for c in columns if c not in listening and c not in profile]
    return {'listening': listening, 'subscription': subscription, 'profile': profile}


def main():
    rows = []
    for month in MONTHS:
        start = time.time()
        test = md.load_month(month)
        y = test[md.LABEL].to_numpy()
        train = md.load_training_sample(training_months(month), PER_MONTH)
        x_train, x_test = md.feature_matrix(train), md.feature_matrix(test)
        fam = families(list(x_train.columns))
        variants = {'all features': list(x_train.columns),
                    'subscription + profile (no listening)': fam['subscription'] + fam['profile'],
                    'listening only': fam['listening'],
                    'subscription only': fam['subscription']}
        for name, columns in variants.items():
            model = md.make_boosting(columns).fit(x_train[columns], train[md.LABEL])
            score = model.predict_proba(x_test[columns])[:, 1]
            for _, row in ev.topk_metrics(y, score).iterrows():
                rows.append({'month': month, 'features': name, 'n_features': len(columns), 'capacity': row['capacity'],
                             'precision': row['precision'], 'recall': row['recall'], 'lift': row['lift'],
                             'auc': ev.auc(y, score)})
        print(f'{month}: {time.time() - start:.0f} s', flush=True)
        OUT.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(OUT / 'ablation.csv', index=False)


if __name__ == '__main__':
    main()
