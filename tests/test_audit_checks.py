import unittest

import duckdb
import pandas as pd

from src import audit_checks as ac


def connection(**tables):
    con = duckdb.connect()
    for name, frame in tables.items():
        con.register(name, pd.DataFrame(frame, dtype='object'))
    return con


class AuditCheckTests(unittest.TestCase):
    def test_table_summary(self):
        con = connection(t={'msno': ['a', 'a', 'b'], 'x': ['1', '2', '3']})
        result = ac.table_summary(con, 't', key='msno')['value']
        self.assertEqual((result['rows'], result['columns'], result['unique_msno']), (3, 2, 2))

    def test_missingness_counts_null_and_blank(self):
        con = connection(t={'a': ['x', None, ' ', 'y'], 'b': ['1', '2', '3', '4']})
        result = ac.missingness(con, 't')
        self.assertEqual(result.loc['a', 'missing'], 2)
        self.assertEqual(result.loc['a', 'percentage'], 50.0)
        self.assertEqual(result.loc['b', 'missing'], 0)

    def test_key_uniqueness(self):
        con = connection(t={'k': ['a', 'a', 'a', 'b', None], 'v': ['1', '2', '3', '4', '5']})
        result = ac.key_uniqueness(con, 't', 'k')['value']
        self.assertEqual(result['rows'], 5)
        self.assertEqual(result['missing_key_rows'], 1)
        self.assertEqual(result['unique_keys'], 2)
        self.assertEqual(result['duplicated_keys'], 1)
        self.assertEqual(result['excess_rows'], 2)
        self.assertEqual(result['rows_in_duplicated_keys'], 3)
        self.assertEqual(result['max_rows_per_key'], 3)

    def test_composite_key_ignores_rows_with_missing_part(self):
        con = connection(t={'k': ['a', 'a', 'a'], 'd': ['1', '1', None]})
        result = ac.key_uniqueness(con, 't', ['k', 'd'])['value']
        self.assertEqual((result['missing_key_rows'], result['excess_rows']), (1, 1))

    def test_exact_duplicates(self):
        con = connection(t={'a': ['x', 'x', 'y'], 'b': ['1', '1', '1']})
        self.assertEqual(ac.exact_duplicates(con, 't')['value']['excess_rows'], 1)
        self.assertEqual(ac.exact_duplicates(con, 't', ['b'])['value']['excess_rows'], 2)

    def test_value_counts_pct_includes_missing(self):
        con = connection(t={'a': ['x', 'x', 'y', None]})
        result = ac.value_counts_pct(con, 't', 'a')
        self.assertEqual(result.iloc[0]['value'], 'x')
        self.assertEqual(result.iloc[0]['count'], 2)
        self.assertEqual(result['percentage'].sum(), 100.0)

    def test_numeric_range(self):
        con = connection(t={'n': ['5', '-3', '0', 'bad', '', None, '1e2']})
        row = ac.numeric_range(con, 't', ['n']).loc['n']
        self.assertEqual((row['missing'], row['non_numeric'], row['negative'], row['zero']), (2, 1, 1, 1))
        self.assertEqual((row['min'], row['max']), (-3.0, 100.0))

    def test_date_validity_rejects_impossible_and_short_dates(self):
        con = connection(t={'d': ['20170301', '20170230', '2017031', None, '20170331']})
        row = ac.date_validity(con, 't', ['d']).loc['d']
        self.assertEqual((row['missing'], row['invalid']), (1, 2))
        self.assertEqual(str(row['earliest'].date()), '2017-03-01')
        self.assertEqual(str(row['latest'].date()), '2017-03-31')

    def test_monthly_coverage(self):
        con = connection(t={'d': ['20170101', '20170102', '20170201'], 'k': ['a', 'a', 'b']})
        result = ac.monthly_coverage(con, 't', 'd', key='k')
        self.assertEqual(result['month'].tolist(), ['2017-01', '2017-02'])
        self.assertEqual(result['rows'].tolist(), [2, 1])
        self.assertEqual(result['keys'].tolist(), [1, 1])

    def test_flag_counts(self):
        con = connection(t={'a': ['1', '2', '3', '4']})
        result = ac.flag_counts(con, 't', {'big': 'CAST(a AS INTEGER) > 2', 'none': 'false'})
        self.assertEqual(result.loc['big', 'rows'], 2)
        self.assertEqual(result.loc['big', 'percentage_of_all_rows'], 50.0)
        self.assertEqual(result.loc['none', 'rows'], 0)

    def test_coverage_uses_distinct_keys(self):
        con = connection(left={'k': ['a', 'a', 'b', 'c', None]}, right={'k': ['a', 'c', 'c', 'z']})
        result = ac.coverage(con, 'left', 'right', 'k')['value']
        self.assertEqual((result['left_keys'], result['matched'], result['unmatched']), (3, 2, 1))
        self.assertAlmostEqual(result['matched_percentage'], 200 / 3)


if __name__ == '__main__':
    unittest.main()
