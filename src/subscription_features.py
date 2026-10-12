"""Subscription-history and profile features per user at a prediction cutoff (DuckDB).

Every feature uses only transactions dated on or before ``cutoff``; members contribute only attributes
that are known by the cutoff (see `docs/prediction_design.md`). A *relation* is a DuckDB table or view
with the nine transaction columns as text (see `src/audit_checks.py`), or the members columns as text.

The user's *last row* follows the official labeller's ordering (`src/churn_labels.py`), so the
``last_*`` fields describe the same row that defines the last expiration used for the population.
Users without any transaction up to the cutoff get ``has_history = False`` and missing values.
"""
from src.churn_labels import _LAST_ROW, _date, _quote

HISTORY_START = '20150101'
FIRST_MONTH_END = '20150131'     # first transactions up to this date may be older subscriptions (left censored)


def subscription_features(con, tx_relation, users_relation, cutoff, history_start=HISTORY_START):
    """One row per user of ``users_relation`` (column ``msno``) with subscription-history features."""
    cutoff, history_start = _date(cutoff), _date(history_start)
    sql = f"""
        WITH cutoff_dates AS (
            SELECT TRY_STRPTIME('{cutoff}', '%Y%m%d') AS cutoff_date,
                   strftime(TRY_STRPTIME('{cutoff}', '%Y%m%d') - INTERVAL 89 DAY, '%Y%m%d') AS start_90),
        t AS (
            SELECT x.msno, payment_method_id, payment_plan_days, plan_list_price, actual_amount_paid,
                   is_auto_renew, transaction_date, membership_expire_date, is_cancel,
                   plan_list_price || payment_plan_days || payment_method_id AS sig
            FROM {_quote(tx_relation)} x
            JOIN (SELECT DISTINCT msno FROM {_quote(users_relation)}) u ON u.msno = x.msno
            WHERE transaction_date >= '{history_start}' AND transaction_date <= '{cutoff}'),
        last_row AS (
            SELECT * FROM (
                SELECT *, row_number() OVER (PARTITION BY msno ORDER BY {_LAST_ROW.format(p='')}) AS rn FROM t)
            WHERE rn = 1),
        plan_changes AS (
            SELECT msno, count(*) FILTER (WHERE prev IS NOT NULL AND prev <> plan_days) AS n_plan_changes
            FROM (SELECT msno, payment_plan_days AS plan_days,
                         lag(payment_plan_days) OVER (PARTITION BY msno
                             ORDER BY transaction_date, membership_expire_date) AS prev
                  FROM t WHERE is_cancel = '0')
            GROUP BY msno),
        agg AS (
            SELECT msno,
                   min(transaction_date) AS first_tx,
                   max(transaction_date) AS last_tx,
                   count(*) AS n_transactions,
                   count(*) FILTER (WHERE is_cancel = '1') AS n_cancellations,
                   count(*) FILTER (WHERE transaction_date >= (SELECT start_90 FROM cutoff_dates)) AS n_transactions_90,
                   count(*) FILTER (WHERE is_cancel = '1'
                                    AND transaction_date >= (SELECT start_90 FROM cutoff_dates)) AS n_cancellations_90,
                   avg((TRY_CAST(actual_amount_paid AS INTEGER) = 0)::INT) FILTER (WHERE is_cancel = '0')
                       AS zero_paid_share,
                   avg(TRY_CAST(is_auto_renew AS INTEGER)) FILTER (WHERE is_cancel = '0') AS auto_renew_share
            FROM t GROUP BY msno)
        SELECT u.msno,
               a.msno IS NOT NULL AS has_history,
               date_diff('day', TRY_STRPTIME(a.first_tx, '%Y%m%d'), (SELECT cutoff_date FROM cutoff_dates)) AS tenure_days,
               a.first_tx <= '{FIRST_MONTH_END}' AS first_tx_in_first_data_month,
               a.n_transactions, a.n_cancellations, a.n_transactions_90, a.n_cancellations_90,
               date_diff('day', TRY_STRPTIME(a.last_tx, '%Y%m%d'), (SELECT cutoff_date FROM cutoff_dates))
                   AS days_since_last_transaction,
               date_diff('day', (SELECT cutoff_date FROM cutoff_dates), TRY_STRPTIME(l.membership_expire_date, '%Y%m%d'))
                   AS days_to_expiration,
               TRY_CAST(l.payment_plan_days AS INTEGER) AS last_plan_days,
               TRY_CAST(l.plan_list_price AS INTEGER) AS last_list_price,
               TRY_CAST(l.actual_amount_paid AS INTEGER) AS last_amount_paid,
               TRY_CAST(l.is_auto_renew AS INTEGER) AS last_auto_renew,
               TRY_CAST(l.payment_method_id AS INTEGER) AS last_payment_method,
               (l.is_cancel = '1') AS last_is_cancel,
               (TRY_CAST(l.actual_amount_paid AS INTEGER) = 0) AS last_paid_zero,
               (TRY_CAST(l.actual_amount_paid AS INTEGER) < TRY_CAST(l.plan_list_price AS INTEGER)) AS last_paid_below_list,
               a.zero_paid_share, a.auto_renew_share,
               coalesce(p.n_plan_changes, 0) AS n_plan_changes
        FROM (SELECT DISTINCT msno FROM {_quote(users_relation)}) u
        LEFT JOIN agg a ON a.msno = u.msno
        LEFT JOIN last_row l ON l.msno = u.msno
        LEFT JOIN plan_changes p ON p.msno = u.msno
        ORDER BY u.msno"""
    return con.sql(sql).df()


def profile_features(con, members_relation, users_relation, cutoff):
    """Profile attributes known by the cutoff, one row per user (columns of the members file as text).

    ``city`` and ``registered_via`` are category codes (meaning unknown), ``gender`` keeps "unknown",
    ``age`` is the supplied age when it lies in 1 to 100 (else missing, ``age_valid`` False), and
    ``registration_days`` counts days from the registration date to the cutoff; a registration after the
    cutoff is treated as unknown (missing). ``has_member_profile`` is returned for diagnostics only and is
    not a model feature until it is shown to be knowable at the cutoff.
    """
    cutoff = _date(cutoff)
    sql = f"""
        SELECT u.msno,
               m.msno IS NOT NULL AS has_member_profile,
               TRY_CAST(m.city AS INTEGER) AS city,
               TRY_CAST(m.registered_via AS INTEGER) AS registered_via,
               coalesce(nullif(m.gender, ''), 'unknown') AS gender,
               CASE WHEN TRY_CAST(m.bd AS INTEGER) BETWEEN 1 AND 100 THEN TRY_CAST(m.bd AS INTEGER) END AS age,
               coalesce(TRY_CAST(m.bd AS INTEGER) BETWEEN 1 AND 100, false) AS age_valid,
               CASE WHEN m.registration_init_time <= '{cutoff}' THEN
                    date_diff('day', TRY_STRPTIME(m.registration_init_time, '%Y%m%d'),
                              TRY_STRPTIME('{cutoff}', '%Y%m%d')) END AS registration_days
        FROM (SELECT DISTINCT msno FROM {_quote(users_relation)}) u
        LEFT JOIN {_quote(members_relation)} m ON m.msno = u.msno
        ORDER BY u.msno"""
    return con.sql(sql).df()
