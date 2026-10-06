"""Rebuild churn labels from transactions with the rules of the official WSDM KKBox labeller (DuckDB).

The official `WSDMChurnLabeller.scala` is the reference (summary in `docs/churn_definition.md`):

1. History = transactions dated from ``history_start`` up to the prediction ``cutoff``. Sort each user's
   history by transaction date, then by plan signature (descending), then non-cancellations before
   cancellations (non-cancellations by ascending, cancellations by descending expiration date), and take
   the expiration date of the last row as the user's *last expiration*.
2. Population = users whose last expiration lies inside the target window.
3. Outcome = the user's transactions after the cutoff, in the same order. A cancellation can move the
   expiration earlier; the first non-cancellation gives a renewal gap (days from the adjusted expiration to
   that transaction). A gap below 30 days is a renewal (``is_churn = 0``); 30 days or more, no later
   transaction, or only cancellations is churn (``is_churn = 1``).

A *relation* is the name of a table or view in the DuckDB connection with the nine transaction columns as
text (see `src/audit_checks.py`). Outcomes need transactions up to about 30 days after the end of the target
window: with data ending on 2017-03-31, reliable rebuilt labels exist only for target months up to 2017-02.
"""
import calendar
import re

import pandas as pd

GRACE_DAYS = 30

# Reverse of the labeller's ordering: row number 1 is the last row of the history.
_LAST_ROW = """{p}transaction_date DESC, {p}sig ASC, {p}is_cancel DESC,
               CASE WHEN {p}is_cancel = '1' THEN {p}membership_expire_date END ASC,
               CASE WHEN {p}is_cancel = '0' THEN {p}membership_expire_date END DESC"""
# The labeller's forward ordering, used for the transactions after the cutoff.
_FORWARD = """{p}transaction_date ASC, {p}sig DESC, {p}is_cancel ASC,
              CASE WHEN {p}is_cancel = '0' THEN {p}membership_expire_date END ASC,
              CASE WHEN {p}is_cancel = '1' THEN {p}membership_expire_date END DESC"""


def _quote(name):
    return '"' + str(name).replace('"', '""') + '"'


def _date(value):
    text = str(value)
    if not re.fullmatch(r'[0-9]{8}', text):
        raise ValueError(f'Expected a YYYYMMDD date, got {value!r}')
    return text


def month_window(target_month):
    """Cutoff and expiration window for a target month ``YYYY-MM``.

    The cutoff is the last day of the previous month (the convention that matches the official
    February and March 2017 labels), the window is the target month itself.
    """
    year, month = (int(part) for part in target_month.split('-'))
    last_day = calendar.monthrange(year, month)[1]
    previous_year, previous_month = (year, month - 1) if month > 1 else (year - 1, 12)
    previous_last_day = calendar.monthrange(previous_year, previous_month)[1]
    return {'cutoff': f'{previous_year:04d}{previous_month:02d}{previous_last_day:02d}',
            'window_start': f'{year:04d}{month:02d}01',
            'window_end': f'{year:04d}{month:02d}{last_day:02d}'}


def _history_sql(relation, cutoff, history_start):
    """CTEs ``t`` (transactions with the plan signature) and ``last_row`` (each user's last expiration)."""
    return f"""
        t AS (
            SELECT msno, transaction_date, membership_expire_date, is_cancel,
                   plan_list_price || payment_plan_days || payment_method_id AS sig
            FROM {_quote(relation)}),
        last_row AS (
            SELECT msno, membership_expire_date AS last_expire
            FROM (SELECT msno, membership_expire_date,
                         row_number() OVER (PARTITION BY msno ORDER BY {_LAST_ROW.format(p='')}) AS rn
                  FROM t WHERE transaction_date >= '{history_start}' AND transaction_date <= '{cutoff}')
            WHERE rn = 1)"""


def last_expirations(con, relation, cutoff, history_start='20150101'):
    """Every user's last expiration at ``cutoff`` (labeller ordering): columns ``msno``, ``last_expire``."""
    cutoff, history_start = _date(cutoff), _date(history_start)
    return con.sql(f"WITH {_history_sql(relation, cutoff, history_start)} SELECT msno, last_expire FROM last_row").df()


def users_expiring_in_window(con, relation, cutoff, window_start, window_end, history_start='20150101'):
    """Users with ANY transaction up to ``cutoff`` whose expiration lies in the window (a looser rule).

    The official training users are covered much better by this rule than by the last-expiration rule
    (exploratory result, see the master plan). Returns a DataFrame with the column ``msno``.
    """
    cutoff, window_start, window_end, history_start = (
        _date(v) for v in (cutoff, window_start, window_end, history_start))
    return con.sql(f"""
        SELECT DISTINCT msno FROM {_quote(relation)}
        WHERE transaction_date >= '{history_start}' AND transaction_date <= '{cutoff}'
          AND membership_expire_date >= '{window_start}' AND membership_expire_date <= '{window_end}'
        ORDER BY msno""").df()


def rebuild_labels(con, relation, cutoff, window_start, window_end, history_start='20150101'):
    """Users whose last expiration at ``cutoff`` lies in the window, with renewal gap and churn label.

    Returns a DataFrame with columns ``msno``, ``last_expire``, ``gap_days`` (missing when the user has no
    later non-cancellation transaction) and ``is_churn`` (1 churn, 0 renewal). Read-only.
    """
    cutoff, window_start, window_end, history_start = (
        _date(v) for v in (cutoff, window_start, window_end, history_start))
    sql = f"""
        WITH {_history_sql(relation, cutoff, history_start)},
        candidates AS (
            SELECT * FROM last_row WHERE last_expire >= '{window_start}' AND last_expire <= '{window_end}'),
        later AS (
            SELECT c.msno, c.last_expire, f.transaction_date, f.is_cancel,
                   min(CASE WHEN f.is_cancel = '1' THEN f.membership_expire_date END)
                       OVER (PARTITION BY c.msno ORDER BY {_FORWARD.format(p='f.')}
                             ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS earlier_cancel_expiry,
                   row_number() OVER (PARTITION BY c.msno, f.is_cancel ORDER BY {_FORWARD.format(p='f.')}) AS rn_in_type
            FROM candidates c JOIN t f ON f.msno = c.msno AND f.transaction_date > '{cutoff}'),
        gaps AS (
            SELECT msno,
                   date_diff('day',
                             TRY_STRPTIME(least(last_expire, coalesce(earlier_cancel_expiry, last_expire)), '%Y%m%d'),
                             TRY_STRPTIME(transaction_date, '%Y%m%d')) AS gap_days
            FROM later WHERE is_cancel = '0' AND rn_in_type = 1)
        SELECT c.msno, c.last_expire, g.gap_days,
               CASE WHEN g.gap_days IS NULL OR g.gap_days >= {GRACE_DAYS} THEN 1 ELSE 0 END AS is_churn
        FROM candidates c LEFT JOIN gaps g USING (msno)
        ORDER BY c.msno"""
    return con.sql(sql).df()


def rebuild_months(con, relation, months, history_start='20150101'):
    """``rebuild_labels`` for several target months, stacked with a ``target_month`` column."""
    frames = []
    for month in months:
        frame = rebuild_labels(con, relation, history_start=history_start, **month_window(month))
        frame.insert(0, 'target_month', month)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
        columns=['target_month', 'msno', 'last_expire', 'gap_days', 'is_churn'])
