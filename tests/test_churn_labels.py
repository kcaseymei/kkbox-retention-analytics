import unittest

import duckdb
import pandas as pd

from src import churn_labels as cl

COLUMNS = ['msno', 'payment_method_id', 'payment_plan_days', 'plan_list_price', 'actual_amount_paid',
           'is_auto_renew', 'transaction_date', 'membership_expire_date', 'is_cancel']
MARCH = dict(cutoff='20170331', window_start='20170301', window_end='20170331')


def tx(user, transaction_date, expire, cancel=0, plan='30', price='149', method='41'):
    return [user, method, plan, price, price, '1', transaction_date, expire, str(cancel)]


def labels(rows, **window):
    con = duckdb.connect()
    con.register('transactions', pd.DataFrame(rows, columns=COLUMNS, dtype='object'))
    return cl.rebuild_labels(con, 'transactions', **(window or MARCH)).set_index('msno')


class OfficialExampleTests(unittest.TestCase):
    """The three illustrative sequences of the competition description (see docs/churn_definition.md)."""

    def test_case_1_late_renewal_is_churn(self):
        result = labels([tx('u', '20170101', '20170228'), tx('u', '20170225', '20170315'),
                         tx('u', '20170430', '20170520')])
        self.assertEqual(result.loc['u', 'last_expire'], '20170315')
        self.assertEqual(result.loc['u', 'gap_days'], 46)
        self.assertEqual(result.loc['u', 'is_churn'], 0 + 1)

    def test_case_2_cancellation_then_timely_renewal_is_retained(self):
        result = labels([tx('u', '20170101', '20170228'), tx('u', '20170225', '20170403'),
                         tx('u', '20170315', '20170316', cancel=1), tx('u', '20170401', '20170630')])
        self.assertEqual(result.loc['u', 'last_expire'], '20170316')
        self.assertEqual(result.loc['u', 'gap_days'], 16)
        self.assertEqual(result.loc['u', 'is_churn'], 0)

    def test_case_3_expiration_outside_the_window_is_excluded(self):
        result = labels([tx('u', '20170101', '20170228'), tx('u', '20170225', '20170403'),
                         tx('u', '20170315', '20170316', cancel=1), tx('u', '20170318', '20170402')])
        self.assertNotIn('u', result.index)


class RuleTests(unittest.TestCase):
    def test_no_later_transaction_is_churn(self):
        result = labels([tx('u', '20170301', '20170331')])
        self.assertEqual(result.loc['u', 'is_churn'], 1)
        self.assertTrue(pd.isna(result.loc['u', 'gap_days']))

    def test_only_later_cancellations_is_churn(self):
        result = labels([tx('u', '20170301', '20170331'), tx('u', '20170405', '20170401', cancel=1)])
        self.assertEqual(result.loc['u', 'is_churn'], 1)

    def test_gap_boundary_is_thirty_days(self):
        result = labels([tx('a', '20170301', '20170331'), tx('a', '20170429', '20170528'),
                         tx('b', '20170301', '20170331'), tx('b', '20170430', '20170529')])
        self.assertEqual((result.loc['a', 'gap_days'], result.loc['a', 'is_churn']), (29, 0))
        self.assertEqual((result.loc['b', 'gap_days'], result.loc['b', 'is_churn']), (30, 1))

    def test_later_cancellation_moves_the_expiration_earlier(self):
        result = labels([tx('u', '20170301', '20170325'), tx('u', '20170405', '20170302', cancel=1),
                         tx('u', '20170415', '20170515')])
        self.assertEqual(result.loc['u', 'gap_days'], 44)
        self.assertEqual(result.loc['u', 'is_churn'], 1)

    def test_same_day_subscription_precedes_cancellation(self):
        result = labels([tx('u', '20170301', '20170331'), tx('u', '20170301', '20170305', cancel=1)])
        self.assertEqual(result.loc['u', 'last_expire'], '20170305')

    def test_history_before_history_start_is_ignored(self):
        result = labels([tx('u', '20160101', '20170315')], history_start='20170101', **MARCH)
        self.assertNotIn('u', result.index)

    def test_invalid_date_is_rejected(self):
        with self.assertRaises(ValueError):
            labels([tx('u', '20170301', '20170331')], cutoff='2017-03-31', window_start='20170301',
                   window_end='20170331')


class PopulationTests(unittest.TestCase):
    def setUp(self):
        self.con = duckdb.connect()
        rows = [tx('inside', '20170110', '20170215'),
                tx('early_renewer', '20170101', '20170220'), tx('early_renewer', '20170125', '20170325'),
                tx('already_expired', '20170101', '20170120'),
                tx('later_only', '20170205', '20170305')]
        self.con.register('transactions', pd.DataFrame(rows, columns=COLUMNS, dtype='object'))

    def test_last_expirations_covers_every_user_with_history(self):
        result = cl.last_expirations(self.con, 'transactions', '20170131').set_index('msno')['last_expire']
        self.assertEqual(result.to_dict(),
                         {'inside': '20170215', 'early_renewer': '20170325', 'already_expired': '20170120'})

    def test_looser_rule_includes_users_with_any_expiration_in_the_window(self):
        window = dict(cutoff='20170131', window_start='20170201', window_end='20170228')
        loose = set(cl.users_expiring_in_window(self.con, 'transactions', **window)['msno'])
        strict = set(cl.rebuild_labels(self.con, 'transactions', **window)['msno'])
        self.assertEqual(strict, {'inside'})
        self.assertEqual(loose, {'inside', 'early_renewer'})


class MonthTests(unittest.TestCase):
    def test_month_window_uses_the_previous_month_end_as_cutoff(self):
        self.assertEqual(cl.month_window('2017-02'),
                         {'cutoff': '20170131', 'window_start': '20170201', 'window_end': '20170228'})
        self.assertEqual(cl.month_window('2016-02')['window_end'], '20160229')
        self.assertEqual(cl.month_window('2017-01')['cutoff'], '20161231')

    def test_rebuild_months_stacks_target_months(self):
        con = duckdb.connect()
        rows = [tx('u', '20170101', '20170215'), tx('u', '20170220', '20170320'),
                tx('v', '20170101', '20170228')]
        con.register('transactions', pd.DataFrame(rows, columns=COLUMNS, dtype='object'))
        result = cl.rebuild_months(con, 'transactions', ['2017-02', '2017-03'])
        self.assertEqual(sorted(result['target_month'].unique()), ['2017-02', '2017-03'])
        # u expires on 02-15 at the January cutoff, then renews on 02-20 and expires on 03-20 at the February cutoff
        self.assertEqual(set(result.loc[result.target_month == '2017-02', 'msno']), {'u', 'v'})
        self.assertEqual(set(result.loc[result.target_month == '2017-03', 'msno']), {'u'})


if __name__ == '__main__':
    unittest.main()
