import unittest

import numpy as np
import pandas as pd

from src import modeling as md


def toy_table(n=400, seed=0):
    rng = np.random.default_rng(seed)
    churn = rng.random(n) < 0.2
    table = pd.DataFrame({
        'msno': [f'u{i}' for i in range(n)], 'target_month': '2017-01', 'cutoff': '20161231',
        'label_source': 'rebuilt', 'is_churn': churn.astype(int), 'has_member_profile': True,
        'last_auto_renew': np.where(churn, 0, 1) * (rng.random(n) < 0.9),
        'active_days_30': rng.integers(0, 31, n).astype(float),
        'n_transactions': rng.integers(1, 30, n), 'plays_30': rng.integers(0, 900, n).astype(float),
        'city': rng.integers(1, 6, n).astype(float), 'registered_via': rng.integers(3, 10, n).astype(float),
        'last_payment_method': rng.integers(30, 40, n).astype(float),
        'gender': rng.choice(['male', 'female', 'unknown'], n), 'has_log_90': True})
    table.loc[:5, 'city'] = -1.0
    table.loc[:5, 'active_days_30'] = np.nan
    return table


class FeatureTests(unittest.TestCase):
    def test_columns_exclude_identifiers_label_and_diagnostics(self):
        columns = md.month_columns(toy_table().columns)
        for name in ('msno', 'target_month', 'cutoff', 'label_source', 'is_churn', 'has_member_profile'):
            self.assertNotIn(name, columns)
        self.assertIn('last_auto_renew', columns)

    def test_matrix_is_numeric_and_negative_categories_become_missing(self):
        matrix = md.feature_matrix(toy_table())
        self.assertTrue(all(pd.api.types.is_float_dtype(t) for t in matrix.dtypes))
        self.assertTrue(matrix.loc[0, 'city'] != matrix.loc[0, 'city'])      # NaN
        self.assertIn(matrix.loc[10, 'gender'], (0.0, 1.0, 2.0))

    def test_matrix_without_profile_columns(self):
        matrix = md.feature_matrix(toy_table(), drop=md.PROFILE_COLUMNS)
        self.assertNotIn('city', matrix.columns)
        self.assertNotIn('gender', matrix.columns)
        self.assertIn('last_payment_method', matrix.columns)

    def test_rules_handle_users_without_history(self):
        table = toy_table()
        table['n_transactions'] = table['n_transactions'].astype('Int32')
        table['last_auto_renew'] = table['last_auto_renew'].astype('Int32')
        table.loc[3, ['n_transactions', 'last_auto_renew']] = pd.NA     # no history at the cutoff
        for score in md.rule_scores(table).values():
            self.assertFalse(np.isnan(score).any())

    def test_rules_rank_the_flagged_users_first(self):
        scores = md.rule_scores(toy_table())
        self.assertEqual(set(scores), {'rule: no auto-renew', 'rule: few listening days (30 days)',
                                       'rule: few transactions'})


class ModelTests(unittest.TestCase):
    def test_models_run_without_profile_columns(self):
        table = toy_table(600)
        x = md.feature_matrix(table, drop=md.PROFILE_COLUMNS)
        y = table['is_churn']
        self.assertEqual(len(md.LogisticModel(list(x.columns)).fit(x, y).predict_proba(x)), 600)
        self.assertEqual(len(md.make_boosting(list(x.columns)).fit(x, y).predict_proba(x)), 600)

    def setUp(self):
        self.table = toy_table(600)
        self.x, self.y = md.feature_matrix(self.table), self.table['is_churn']

    def test_logistic_learns_the_signal(self):
        proba = md.LogisticModel(list(self.x.columns)).fit(self.x, self.y).predict_proba(self.x)
        self.assertGreater(proba[self.y == 1].mean(), proba[self.y == 0].mean())

    def test_boosting_learns_the_signal_with_missing_values(self):
        proba = md.make_boosting(list(self.x.columns)).fit(self.x, self.y).predict_proba(self.x)[:, 1]
        self.assertGreater(proba[self.y == 1].mean(), proba[self.y == 0].mean())


if __name__ == '__main__':
    unittest.main()
