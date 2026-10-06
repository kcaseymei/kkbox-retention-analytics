"""Readable notebook output: a bold title above a formatted table.

``format_table`` turns a DataFrame or Series into a table of display strings (thousands
separators, percentages with a % sign, dates without a time part, a dash for missing values).
``show`` displays the title, an optional note, and that table. Display only: it never changes
the data it is given.
"""
import math
import numbers

import pandas as pd


def _is_percent(label):
    text = str(label).lower()
    return 'percentage' in text or text.endswith('_pct') or text == 'pct'


def _format_value(value, percent=False):
    if value is None or value is pd.NaT or (isinstance(value, float) and math.isnan(value)):
        return '–'
    if isinstance(value, pd.Timestamp):
        return value.strftime('%Y-%m-%d') if value == value.normalize() else value.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, numbers.Integral):
        return f'{int(value):,}%' if percent else f'{int(value):,}'
    if isinstance(value, numbers.Real):
        number = float(value)
        if percent:
            return '<0.01%' if 0 < number < 0.01 else f'{number:,.2f}%'
        if number.is_integer():
            return f'{int(number):,}'
        if number != 0 and abs(number) < 0.01:
            return f'{number:.3g}'
        return f'{number:,.2f}'
    return str(value)


def format_table(data, max_rows=None):
    """Return a same-shaped DataFrame of display strings."""
    frame = data.to_frame() if isinstance(data, pd.Series) else data
    if max_rows is not None:
        frame = frame.head(max_rows)
    cells = [[_format_value(frame.iat[i, j], _is_percent(frame.columns[j]) or _is_percent(frame.index[i]))
              for j in range(frame.shape[1])] for i in range(frame.shape[0])]
    return pd.DataFrame(cells, index=frame.index, columns=frame.columns)


def show(title, data, note=None, max_rows=50):
    """Display ``title`` (bold), an optional italic ``note``, then the formatted table."""
    from IPython.display import Markdown, display
    display(Markdown(f'**{title}**' + (f'  \n*{note}*' if note else '')))
    table = format_table(data, max_rows=max_rows)
    display(table.style.set_properties(**{'text-align': 'right'}))
    if max_rows is not None and len(data) > max_rows:
        display(Markdown(f'*Showing the first {max_rows:,} of {len(data):,} rows.*'))
