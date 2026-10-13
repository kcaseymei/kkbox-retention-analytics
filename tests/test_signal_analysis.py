import unittest

import numpy as np
import pandas as pd

from src import signal_analysis as sa


def users(rows):
    return pd.DataFrame(rows, columns=['active_days_30', 'active_days_60', 'has_log_90'])


class DeclineGroupTests(unittest.TestCase):
    def groups(self, rows):
        frame = users(rows)
        return list(sa.decline_group(frame['active_days_30'], frame['active_days_60'], frame['has_log_90']))

    def test_groups_and_boundaries(self):
        # prior = active_60 - active_30
        result = self.groups([
            (0, 10, True),      # prior 10, last 30 days 0 -> stopped
            (7, 17, True),      # prior 10, 7 days (-30%) -> declined
            (8, 18, True),      # prior 10, 8 days (-20%) -> stable
            (7.5, 17.5, True),  # exactly -25% -> stable (declined means strictly more than 25%)
            (13, 23, True),     # +30% -> increased
            (12.5, 22.5, True)])  # exactly +25% -> stable
        self.assertEqual(result, [sa.DECLINE_GROUPS[0], sa.DECLINE_GROUPS[1], sa.DECLINE_GROUPS[2],
                                  sa.DECLINE_GROUPS[2], sa.DECLINE_GROUPS[3], sa.DECLINE_GROUPS[2]])

    def test_users_without_prior_listening_are_not_comparable(self):
        result = self.groups([(5, 5, True),            # prior 0
                              (np.nan, np.nan, False),  # no log in 90 days
                              (3, 13, False)])
        self.assertTrue(all(g is None for g in result))


class TableTests(unittest.TestCase):
    def frame(self):
        rows = []
        # 10 stable users (2 churn), 10 declined users (6 churn)
        for i in range(10):
            rows.append(('2017-02', 'rebuilt', int(i < 2), True, 10, 20, 1))
        for i in range(10):
            rows.append(('2017-02', 'rebuilt', int(i < 6), True, 4, 14, 0))
        return pd.DataFrame(rows, columns=['target_month', 'label_source', 'is_churn', 'has_log_90',
                                           'active_days_30', 'active_days_60', 'last_auto_renew'])

    def test_decline_table_rates_and_ratio(self):
        row = sa.decline_table(self.frame()).iloc[0]
        self.assertEqual(row['comparable_users'], 20)
        self.assertAlmostEqual(row['churn_rate_stable (within 25%)'], 20.0)
        self.assertAlmostEqual(row['churn_rate_declined (more than 25%)'], 60.0)
        self.assertAlmostEqual(row['risk_ratio_fell_or_stopped_vs_stable'], 3.0)

    def test_renewal_mode_shares(self):
        row = sa.renewal_mode_table(self.frame()).iloc[0]
        self.assertAlmostEqual(row['manual_share_of_users'], 50.0)
        self.assertAlmostEqual(row['manual_share_of_churners'], 100 * 6 / 8)
        self.assertAlmostEqual(row['risk_ratio_manual_vs_auto'], 3.0)

    def test_cross_table_keeps_renewal_mode_fixed(self):
        table = sa.decline_by_renewal_mode(self.frame())
        self.assertEqual(set(table['renewal_mode']), {'manual (auto-renew off)', 'auto-renew on'})
        self.assertEqual(int(table['users'].sum()), 20)

    def test_unknown_renewal_mode_is_left_out(self):
        frame = self.frame()
        frame.loc[0, 'last_auto_renew'] = np.nan
        self.assertEqual(int(sa.renewal_mode_table(frame).iloc[0]['users']), 19)


if __name__ == '__main__':
    unittest.main()
