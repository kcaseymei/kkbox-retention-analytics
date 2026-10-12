"""Train and evaluate the rules and models with time-ordered splits (run from the repository root).

    python -m src.run_experiments            # about 25 minutes; writes reports/model_results/*.csv

Protocol (see `docs/prediction_design.md`): to predict month M, train only on months whose labels are complete
by M's cutoff (`leakage_checks.check_purge`: months up to M-2, and before March also excluding M-2), using a
random sample of users per month; evaluate on every user of M. Settings are fixed (no tuning).

* validation: 2016-07 to 2016-12 (rebuilt labels), expanding window
* final test: 2017-01 and 2017-02 (rebuilt labels)
* external check: 2017-03 (official labels, different treatment of early renewers), reported separately

Model variants without the profile columns test how much the members snapshot (a later file) contributes.
"""
import argparse
import time

import pandas as pd
from sklearn.inspection import permutation_importance

from src import evaluation as ev
from src import leakage_checks as lc
from src import modeling as md
from src.build_features import REBUILT_MONTHS

OUT = md.OUT_DIR.parent.parent.parent / 'reports' / 'model_results'
PER_MONTH = 100_000
SPLITS = ([('validation', m) for m in REBUILT_MONTHS[REBUILT_MONTHS.index('2016-07'):REBUILT_MONTHS.index('2016-12') + 1]]
          + [('test', '2017-01'), ('test', '2017-02'), ('external', '2017-03')])


def training_months(month):
    """Rebuilt months whose labels are complete by the cutoff of ``month``."""
    months = [m for m in REBUILT_MONTHS if lc.check_purge([m], month)]
    assert lc.check_purge(months, month) and all(m < month for m in months)
    return months


def evaluate(split, month, model, score, y, lead, results, bands, calibration, probability=None):
    top = ev.topk_metrics(y, score)
    for _, row in top.iterrows():
        results.append({'split': split, 'month': month, 'model': model, 'capacity': row['capacity'],
                        'precision': row['precision'], 'recall': row['recall'], 'lift': row['lift'],
                        'base_rate': row['base_rate'], 'auc': ev.auc(y, score),
                        'brier': ev.brier(y, probability) if probability is not None else None})
    if split != 'validation':
        band = ev.band_metrics(y, score, lead, 0.10)
        band.insert(0, 'model', model); band.insert(0, 'month', month)
        bands.append(band)
        if probability is not None:
            table = ev.calibration_table(y, probability).reset_index()
            table.insert(0, 'model', model); table.insert(0, 'month', month)
            calibration.append(table)


def write(results, bands, calibration, importance):
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(OUT / 'results.csv', index=False)
    if bands:
        pd.concat(bands).to_csv(OUT / 'lead_time_bands.csv', index=False)
    if calibration:
        pd.concat(calibration).to_csv(OUT / 'calibration.csv', index=False)
    if importance is not None:
        importance.to_csv(OUT / 'feature_importance_2017-01.csv', index=False)


def _existing(name, rerun):
    """Rows of an earlier output file for months that are not being rerun."""
    path = OUT / name
    if not path.exists():
        return pd.DataFrame()
    table = pd.read_csv(path)
    return table[~table['month'].isin(rerun)]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--months', nargs='*', default=None,
                        help='rerun only these months and keep the saved rows of the others')
    args = parser.parse_args()
    rerun = set(args.months or [])
    results = _existing('results.csv', rerun).to_dict('records') if rerun else []
    bands = [b] if rerun and not (b := _existing('lead_time_bands.csv', rerun)).empty else []
    calibration = [c] if rerun and not (c := _existing('calibration.csv', rerun)).empty else []
    importance = (pd.read_csv(OUT / 'feature_importance_2017-01.csv')
                  if rerun and '2017-01' not in rerun and (OUT / 'feature_importance_2017-01.csv').exists() else None)
    for split, month in SPLITS:
        if rerun and month not in rerun:
            continue
        start = time.time()
        test = md.load_month(month)
        y = test[md.LABEL].to_numpy()
        lead = pd.cut(test['days_to_expiration'], md.LEAD_BANDS, labels=md.LEAD_LABELS).astype(str)
        for name, score in md.rule_scores(test).items():
            evaluate(split, month, name, score, y, lead, results, bands, calibration)
        months = training_months(month)
        train = md.load_training_sample(months, PER_MONTH)
        y_train = train[md.LABEL]
        for variant, drop in (('', ()), (' (no profile columns)', md.PROFILE_COLUMNS)):
            x_train, x_test = md.feature_matrix(train, drop), md.feature_matrix(test, drop)
            columns = list(x_train.columns)
            p_logistic = md.LogisticModel(columns).fit(x_train, y_train).predict_proba(x_test)
            evaluate(split, month, 'logistic regression' + variant, p_logistic, y, lead, results, bands, calibration, p_logistic)
            boosting = md.make_boosting(columns).fit(x_train, y_train)
            p_boosting = boosting.predict_proba(x_test)[:, 1]
            evaluate(split, month, 'gradient boosting' + variant, p_boosting, y, lead, results, bands, calibration, p_boosting)
            if (split, month, variant) == ('test', '2017-01', ''):
                sample = x_test.assign(_y=y).sample(60_000, random_state=0)
                fitted = permutation_importance(boosting, sample.drop(columns='_y'), sample['_y'], scoring='roc_auc',
                                                n_repeats=3, random_state=0, n_jobs=-1)
                importance = pd.DataFrame({'feature': sample.drop(columns='_y').columns,
                                           'auc_drop': fitted.importances_mean}).sort_values('auc_drop', ascending=False)
        print(f'{split} {month}: {len(train):,} training rows from {len(months)} months, '
              f'{time.time() - start:.0f} s', flush=True)
        write(results, bands, calibration, importance)


if __name__ == '__main__':
    main()
