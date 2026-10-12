import unittest

import duckdb
import numpy as np
import pandas as pd

from src import leakage_checks as lc

LOG_COLUMNS = ['msno', 'date', 'num_25', 'num_50', 'num_75', 'num_985', 'num_100', 'num_unq', 'total_secs']
TX_COLUMNS = ['msno', 'payment_method_id', 'payment_plan_days', 'plan_list_price', 'actual_amount_paid',
              'is_auto_renew', 'transaction_date', 'membership_expire_date', 'is_cancel']


class CompareFramesTests(unittest.TestCase):
    def test_detects_changed_values_and_ignores_matching_missing(self):
        a = pd.DataFrame({'msno': ['u', 'v'], 'x': [1.0, np.nan], 'flag': [True, False]})
        b = pd.DataFrame({'msno': ['u', 'v'], 'x': [2.0, np.nan], 'flag': [True, True]})
        result = lc.compare_frames(a, b)
        self.assertEqual(result.loc['x', 'rows_differing'], 1)
        self.assertEqual(result.loc['flag', 'rows_differing'], 1)

    def test_float_rounding_is_not_a_difference(self):
        a = pd.DataFrame({'msno': ['u'], 'x': [1234567.1234567]})
        b = pd.DataFrame({'msno': ['u'], 'x': [1234567.1234567 + 4e-9]})
        self.assertEqual(int(lc.compare_frames(a, b)['rows_differing'].sum()), 0)

    def test_identical_frames_have_no_differences(self):
        a = pd.DataFrame({'msno': ['u'], 'x': [1.0]})
        self.assertEqual(int(lc.compare_frames(a, a.copy())['rows_differing'].sum()), 0)


class InvarianceTests(unittest.TestCase):
    def test_features_do_not_change_when_later_data_is_removed(self):
        con = duckdb.connect()
        logs = [['a', d, '1', '1', '1', '1', '1', '5', '100'] for d in ('20170120', '20170131', '20170205', '20170220')]
        tx = [['a', '41', '30', '149', '149', '1', d, e, '0'] for d, e in
              (('20170101', '20170215'), ('20170210', '20170315'), ('20170301', '20170401'))]
        con.register('logs', pd.DataFrame(logs, columns=LOG_COLUMNS, dtype='object'))
        con.register('tx', pd.DataFrame(tx, columns=TX_COLUMNS, dtype='object'))
        con.register('users', pd.DataFrame({'msno': ['a']}))
        result = lc.check_cutoff_invariance(con, 'logs', 'tx', 'users', '20170131')
        self.assertEqual(int(result['rows_differing'].sum()), 0)
        self.assertEqual(set(result['group']), {'listening', 'subscription'})


class AucTests(unittest.TestCase):
    def test_perfect_feature_is_flagged_and_noise_is_not(self):
        rng = np.random.default_rng(0)
        y = np.array([0] * 500 + [1] * 500)
        frame = pd.DataFrame({'is_churn': y, 'leaky': y * 10.0 + rng.normal(0, 0.1, 1000),
                              'noise': rng.normal(size=1000)})
        auc = lc.single_feature_auc(frame)
        self.assertGreater(auc['leaky'], lc.AUC_ALERT)
        self.assertLess(auc['noise'], 0.6)

    def test_orientation_and_missing_values(self):
        frame = pd.DataFrame({'is_churn': [0, 0, 1, 1], 'inverse': [4.0, 3.0, 2.0, np.nan]})
        self.assertAlmostEqual(lc.single_feature_auc(frame)['inverse'], 1.0)


class SplitTests(unittest.TestCase):
    def test_purge_rule(self):
        self.assertTrue(lc.check_purge(['2016-10', '2016-11'], '2017-01'))
        self.assertFalse(lc.check_purge(['2016-10', '2016-12'], '2017-01'))
        self.assertTrue(lc.check_purge(['2015-07'], '2017-02'))

    def test_duplicate_rows(self):
        frame = pd.DataFrame({'msno': ['u', 'u', 'v'], 'target_month': ['2017-01', '2017-01', '2017-01']})
        self.assertEqual(lc.check_unique_rows(frame), 1)


if __name__ == '__main__':
    unittest.main()
