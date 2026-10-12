import unittest

import duckdb
import pandas as pd

from src import subscription_features as sf

TX_COLUMNS = ['msno', 'payment_method_id', 'payment_plan_days', 'plan_list_price', 'actual_amount_paid',
              'is_auto_renew', 'transaction_date', 'membership_expire_date', 'is_cancel']
MEMBER_COLUMNS = ['msno', 'city', 'bd', 'gender', 'registered_via', 'registration_init_time']
CUTOFF = '20170131'


def tx(user, date, expire, cancel=0, plan='30', price='149', paid=None, auto='1', method='41'):
    return [user, method, plan, price, price if paid is None else paid, auto, date, expire, str(cancel)]


def features(rows, users):
    con = duckdb.connect()
    con.register('tx', pd.DataFrame(rows, columns=TX_COLUMNS, dtype='object'))
    con.register('users', pd.DataFrame({'msno': users}))
    return sf.subscription_features(con, 'tx', 'users', CUTOFF).set_index('msno')


class SubscriptionTests(unittest.TestCase):
    def test_counts_tenure_and_last_row(self):
        rows = [tx('a', '20160101', '20160201'), tx('a', '20161215', '20170115', plan='30'),
                tx('a', '20170115', '20170214', auto='0')]
        row = features(rows, ['a']).loc['a']
        self.assertEqual(row['n_transactions'], 3)
        self.assertEqual(row['tenure_days'], 396)
        self.assertEqual(row['days_to_expiration'], 14)
        self.assertEqual(row['last_auto_renew'], 0)
        self.assertAlmostEqual(row['auto_renew_share'], 2 / 3)
        self.assertEqual(row['days_since_last_transaction'], 16)

    def test_transactions_after_the_cutoff_are_ignored(self):
        rows = [tx('a', '20170101', '20170215'), tx('a', '20170210', '20170315'), tx('a', '20170301', '20170401')]
        row = features(rows, ['a']).loc['a']
        self.assertEqual(row['n_transactions'], 1)
        self.assertEqual(row['days_to_expiration'], 15)

    def test_user_without_history_is_flagged_and_missing(self):
        row = features([tx('a', '20170101', '20170215')], ['a', 'none']).loc['none']
        self.assertFalse(row['has_history'])
        self.assertTrue(pd.isna(row['n_transactions']) and pd.isna(row['tenure_days']))

    def test_cancellations_and_recent_activity(self):
        rows = [tx('a', '20160101', '20160201'), tx('a', '20161103', '20161203'),
                tx('a', '20161115', '20161116', cancel=1), tx('a', '20170105', '20170205')]
        row = features(rows, ['a']).loc['a']
        self.assertEqual((row['n_cancellations'], row['n_cancellations_90']), (1, 1))
        self.assertEqual(row['n_transactions_90'], 3)       # 2016-11-03 is the first day of the window

    def test_plan_changes_ignore_cancellations(self):
        rows = [tx('a', '20160101', '20160201', plan='30'), tx('a', '20160201', '20160301', plan='7'),
                tx('a', '20160210', '20160211', cancel=1, plan='30'), tx('a', '20160301', '20160401', plan='30')]
        self.assertEqual(features(rows, ['a']).loc['a', 'n_plan_changes'], 2)

    def test_zero_price_flags(self):
        rows = [tx('a', '20161201', '20170101', paid='0'), tx('a', '20170101', '20170201', paid='100')]
        row = features(rows, ['a']).loc['a']
        self.assertAlmostEqual(row['zero_paid_share'], 0.5)
        self.assertFalse(row['last_paid_zero'])
        self.assertTrue(row['last_paid_below_list'])

    def test_first_transaction_in_first_data_month_is_flagged(self):
        rows = [tx('a', '20150115', '20150215'), tx('b', '20150301', '20150401')]
        result = features(rows, ['a', 'b'])
        self.assertTrue(result.loc['a', 'first_tx_in_first_data_month'])
        self.assertFalse(result.loc['b', 'first_tx_in_first_data_month'])


class ProfileTests(unittest.TestCase):
    def run_profile(self, rows, users):
        con = duckdb.connect()
        con.register('members', pd.DataFrame(rows, columns=MEMBER_COLUMNS, dtype='object'))
        con.register('users', pd.DataFrame({'msno': users}))
        return sf.profile_features(con, 'members', 'users', CUTOFF).set_index('msno')

    def test_profile_cleaning_and_missing_profile(self):
        rows = [['a', '1', '25', 'female', '7', '20160131'], ['b', '5', '0', '', '9', '20170201']]
        result = self.run_profile(rows, ['a', 'b', 'c'])
        self.assertEqual((result.loc['a', 'age'], result.loc['a', 'registration_days']), (25, 366))
        self.assertEqual(result.loc['b', 'gender'], 'unknown')
        self.assertFalse(result.loc['b', 'age_valid'])
        self.assertTrue(pd.isna(result.loc['b', 'registration_days']))   # registered after the cutoff
        self.assertFalse(result.loc['c', 'has_member_profile'])
        self.assertEqual(result.loc['c', 'gender'], 'unknown')


if __name__ == '__main__':
    unittest.main()
