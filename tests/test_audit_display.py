import unittest

import numpy as np
import pandas as pd

from src.audit_display import format_table


class FormatTableTests(unittest.TestCase):
    def test_integers_and_integer_valued_floats_get_thousands_separators(self):
        table = format_table(pd.DataFrame({'rows': [1234567, 2.0], 'x': [5.0, 1500.0]}))
        self.assertEqual(table['rows'].tolist(), ['1,234,567', '2'])
        self.assertEqual(table['x'].tolist(), ['5', '1,500'])

    def test_percentage_columns_and_percentage_rows(self):
        by_column = format_table(pd.DataFrame({'percentage': [8.9942, 100.0]}))
        self.assertEqual(by_column['percentage'].tolist(), ['8.99%', '100.00%'])
        by_row = format_table(pd.Series({'matched': 801490.0, 'matched_percentage': 88.32128}, name='value'))
        self.assertEqual(by_row['value'].tolist(), ['801,490', '88.32%'])

    def test_tiny_nonzero_percentages_are_not_shown_as_zero(self):
        table = format_table(pd.DataFrame({'percentage': [0.0042, 0.0, 0.01]}))
        self.assertEqual(table['percentage'].tolist(), ['<0.01%', '0.00%', '0.01%'])

    def test_dates_missing_values_and_small_numbers(self):
        frame = pd.DataFrame({'earliest': [pd.Timestamp('2015-01-01'), pd.NaT], 'v': [0.001, np.nan]})
        table = format_table(frame)
        self.assertEqual(table['earliest'].tolist(), ['2015-01-01', '–'])
        self.assertEqual(table['v'].tolist(), ['0.001', '–'])

    def test_series_input_and_row_limit_leave_source_unchanged(self):
        series = pd.Series({'a': 1000, 'b': 2000, 'c': 3000}, name='value')
        table = format_table(series, max_rows=2)
        self.assertEqual(table.shape, (2, 1))
        self.assertEqual(series.tolist(), [1000, 2000, 3000])

    def test_text_and_booleans_pass_through(self):
        table = format_table(pd.DataFrame({'t': ['abc', 'def'], 'b': [True, False]}))
        self.assertEqual(table['t'].tolist(), ['abc', 'def'])
        self.assertEqual(table['b'].tolist(), ['True', 'False'])


if __name__ == '__main__':
    unittest.main()
