"""Listening features per user at a prediction cutoff (DuckDB).

Every feature uses only log rows dated on or before ``cutoff`` (nothing after it), looking back over
windows of 7, 14, 30, 60, and 90 days that include the cutoff day (see `docs/prediction_design.md`).

A *relation* is a DuckDB table or view with the user-log columns as text (``msno``, ``date`` as
``YYYYMMDD``, ``num_25``, ``num_50``, ``num_75``, ``num_985``, ``num_100``, ``num_unq``, ``total_secs``).
Users without any log in the 90-day window get ``has_log_90 = False`` and missing (NULL) feature values:
absent listening is not zero listening. ``total_secs`` outside 0 to 86,400 is treated as missing and the
user is flagged in ``has_invalid_secs_90`` (DQ-001); source values are not altered. A user whose seconds in a window
are all invalid gets ``secs_w = 0`` (plus the flag), not a missing value.
"""
import re
from datetime import datetime, timedelta

import pandas as pd

WINDOWS = (7, 14, 30, 60, 90)


def _quote(name):
    return '"' + str(name).replace('"', '""') + '"'


def _date(value):
    text = str(value)
    if not re.fullmatch(r'[0-9]{8}', text):
        raise ValueError(f'Expected a YYYYMMDD date, got {value!r}')
    return text


def window_start(cutoff, days):
    """First day (YYYYMMDD) of a window of ``days`` days that ends on, and includes, the cutoff."""
    end = datetime.strptime(_date(cutoff), '%Y%m%d')
    return (end - timedelta(days=days - 1)).strftime('%Y%m%d')


def listening_features(con, logs_relation, users_relation, cutoff):
    """One row per user of ``users_relation`` (column ``msno``) with listening features at ``cutoff``.

    Per window w: ``active_days_w``, ``plays_w`` (all play counts), ``secs_w`` (valid seconds),
    ``unique_songs_w`` (sum of daily unique songs) and ``completed_share_w`` (share of plays that reached
    at least 98.5% of the song). Also ``days_since_last_log``, two trend features, and three flags.
    """
    cutoff = _date(cutoff)
    starts = {w: window_start(cutoff, w) for w in WINDOWS}
    inner = ',\n           '.join(
        f"""count(*) FILTER (WHERE l.date >= '{starts[w]}') AS active_days_{w},
           sum(l.plays) FILTER (WHERE l.date >= '{starts[w]}') AS plays_{w},
           sum(l.secs) FILTER (WHERE l.date >= '{starts[w]}') AS secs_{w},
           sum(l.unq) FILTER (WHERE l.date >= '{starts[w]}') AS unique_songs_{w},
           sum(l.completed) FILTER (WHERE l.date >= '{starts[w]}') AS completed_{w}""" for w in WINDOWS)
    outer = ',\n           '.join(
        f"""CASE WHEN has_log_90 THEN active_days_{w} END AS active_days_{w},
           CASE WHEN has_log_90 THEN coalesce(plays_{w}, 0) END AS plays_{w},
           CASE WHEN has_log_90 THEN coalesce(secs_{w}, 0) END AS secs_{w},
           CASE WHEN has_log_90 THEN coalesce(unique_songs_{w}, 0) END AS unique_songs_{w},
           completed_{w}::DOUBLE / nullif(plays_{w}, 0) AS completed_share_{w}""" for w in WINDOWS)
    sql = f"""
        WITH l AS (
            SELECT msno, date,
                   coalesce(TRY_CAST(num_25 AS BIGINT), 0) + coalesce(TRY_CAST(num_50 AS BIGINT), 0)
                     + coalesce(TRY_CAST(num_75 AS BIGINT), 0) + coalesce(TRY_CAST(num_985 AS BIGINT), 0)
                     + coalesce(TRY_CAST(num_100 AS BIGINT), 0) AS plays,
                   coalesce(TRY_CAST(num_985 AS BIGINT), 0) + coalesce(TRY_CAST(num_100 AS BIGINT), 0) AS completed,
                   TRY_CAST(num_unq AS BIGINT) AS unq,
                   CASE WHEN TRY_CAST(total_secs AS DOUBLE) BETWEEN 0 AND 86400
                        THEN TRY_CAST(total_secs AS DOUBLE) END AS secs,
                   NOT (TRY_CAST(total_secs AS DOUBLE) BETWEEN 0 AND 86400) AS bad_secs
            FROM {_quote(logs_relation)}
            WHERE date >= '{starts[90]}' AND date <= '{cutoff}'),
        agg AS (
            SELECT u.msno,
                   count(l.date) > 0 AS has_log_90,
                   coalesce(bool_or(l.bad_secs), false) AS has_invalid_secs_90,
                   date_diff('day', TRY_STRPTIME(max(l.date), '%Y%m%d'), TRY_STRPTIME('{cutoff}', '%Y%m%d'))
                       AS days_since_last_log,
                   {inner}
            FROM (SELECT DISTINCT msno FROM {_quote(users_relation)}) u
            LEFT JOIN l ON l.msno = u.msno
            GROUP BY u.msno)
        SELECT msno, has_log_90, (NOT has_log_90) AS no_log_90_flag, has_invalid_secs_90, days_since_last_log,
               {outer},
               active_days_7 / 7.0 - (active_days_30 - active_days_7) / 23.0 AS trend_days_7_vs_prior_23,
               active_days_30 / 30.0 - (active_days_60 - active_days_30) / 30.0 AS trend_days_30_vs_prior_30
        FROM agg
        ORDER BY msno"""
    return con.sql(sql).df()
