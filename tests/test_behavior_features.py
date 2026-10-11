import unittest

import duckdb
import pandas as pd

from src import behavior_features as bf

COLUMNS = ['msno', 'date', 'num_25', 'num_50', 'num_75', 'num_985', 'num_100', 'num_unq', 'total_secs']
CUTOFF = '20170131'


def log(user, date, plays=10, secs='1000', unq=8, completed=5):
    return [user, date, '0', '0', str(plays - completed), '0', str(completed), str(unq), secs]


def features(rows, users):
    con = duckdb.connect()
    con.register('logs', pd.DataFrame(rows, columns=COLUMNS, dtype='object'))
    con.register('users', pd.DataFrame({'msno': users}))
    return bf.listening_features(con, 'logs', 'users', CUTOFF).set_index('msno')


class WindowTests(unittest.TestCase):
    def test_window_start_includes_the_cutoff_day(self):
        self.assertEqual(bf.window_start('20170131', 7), '20170125')
        self.assertEqual(bf.window_start('20170131', 30), '20170102')
        self.assertEqual(bf.window_start('20170131', 90), '20161103')

    def test_window_boundaries(self):
        result = features([log('a', '20170125'), log('a', '20170124'), log('a', '20170131')], ['a'])
        self.assertEqual(result.loc['a', 'active_days_7'], 2)      # 01-24 is outside the 7-day window
        self.assertEqual(result.loc['a', 'active_days_14'], 3)

    def test_rows_after_the_cutoff_are_ignored(self):
        result = features([log('a', '20170131'), log('a', '20170201'), log('a', '20170215')], ['a'])
        self.assertEqual(result.loc['a', 'active_days_90'], 1)
        self.assertEqual(result.loc['a', 'days_since_last_log'], 0)

    def test_rows_before_the_90_day_window_are_ignored(self):
        result = features([log('a', '20161102'), log('b', '20161103')], ['a', 'b'])
        self.assertFalse(result.loc['a', 'has_log_90'])
        self.assertTrue(result.loc['b', 'has_log_90'])


class MissingBehaviorTests(unittest.TestCase):
    def test_user_without_logs_is_flagged_and_missing_not_zero(self):
        result = features([log('a', '20170130')], ['a', 'none'])
        row = result.loc['none']
        self.assertFalse(row['has_log_90'])
        self.assertTrue(row['no_log_90_flag'])
        self.assertTrue(pd.isna(row['active_days_30']) and pd.isna(row['secs_30']))

    def test_user_with_old_logs_has_zero_recent_activity(self):
        result = features([log('a', '20161110')], ['a'])
        self.assertEqual(result.loc['a', 'active_days_7'], 0)
        self.assertEqual(result.loc['a', 'plays_7'], 0)
        self.assertEqual(result.loc['a', 'days_since_last_log'], 82)


class ValueTests(unittest.TestCase):
    def test_sums_and_shares(self):
        result = features([log('a', '20170130', plays=10, completed=5, secs='600', unq=4),
                           log('a', '20170129', plays=10, completed=10, secs='400', unq=6)], ['a'])
        row = result.loc['a']
        self.assertEqual((row['plays_7'], row['secs_7'], row['unique_songs_7']), (20, 1000.0, 10))
        self.assertAlmostEqual(row['completed_share_7'], 0.75)

    def test_invalid_seconds_are_missing_and_flagged(self):
        result = features([log('a', '20170130', secs='-5'), log('a', '20170129', secs='90000'),
                           log('a', '20170128', secs='300')], ['a'])
        row = result.loc['a']
        self.assertEqual(row['secs_7'], 300.0)
        self.assertEqual(row['active_days_7'], 3)
        self.assertTrue(row['has_invalid_secs_90'])

    def test_trends(self):
        # 7 active days in the last 7 days, none before: rate 1.0 against 0 in the prior 23 days
        rows = [log('a', f'201701{d:02d}') for d in range(25, 32)]
        result = features(rows, ['a'])
        self.assertAlmostEqual(result.loc['a', 'trend_days_7_vs_prior_23'], 1.0)
        self.assertAlmostEqual(result.loc['a', 'trend_days_30_vs_prior_30'], 7 / 30)

    def test_invalid_date_is_rejected(self):
        with self.assertRaises(ValueError):
            bf.window_start('2017-01-31', 7)


if __name__ == '__main__':
    unittest.main()
