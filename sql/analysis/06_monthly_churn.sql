-- Question: for each target month, how many users expire and how many do not renew within 30 days?
-- Rule (simplified from docs/churn_definition.md, non-cancel transactions only):
--   cutoff = last day of the previous month; population = users whose last expiration at the cutoff lies
--   in the target month; churn = no later transaction, or the next one is 30+ days after the expiration.
-- One pass: lead() gives each transaction's successor; a transaction is the "last one at cutoff c"
-- when it happened on or before c and its successor happened after c.
-- Target months 2015-07 to 2017-02 (2015-02..06 is burn-in; later months lack complete outcomes).
WITH tx AS (
    SELECT msno, transaction_date, membership_expire_date,
           lead(transaction_date) OVER (PARTITION BY msno
                                        ORDER BY transaction_date, membership_expire_date) AS next_tx_date
    FROM analytics.transactions
    WHERE is_cancel = 0),
months AS (
    SELECT m::date AS target_month, (m - interval '1 day')::date AS cutoff,
           (m + interval '1 month' - interval '1 day')::date AS month_end
    FROM generate_series('2015-07-01'::date, '2017-02-01'::date, interval '1 month') AS m),
cohort AS (
    SELECT mo.target_month, t.msno,
           (t.next_tx_date IS NULL OR t.next_tx_date - t.membership_expire_date >= 30) AS is_churn
    FROM months mo
    JOIN tx t ON t.transaction_date <= mo.cutoff
             AND (t.next_tx_date IS NULL OR t.next_tx_date > mo.cutoff)
             AND t.membership_expire_date BETWEEN mo.target_month AND mo.month_end)
SELECT to_char(target_month, 'YYYY-MM') AS target_month,
       count(DISTINCT msno) AS users,
       count(DISTINCT msno) FILTER (WHERE is_churn) AS churned,
       round(100.0 * count(DISTINCT msno) FILTER (WHERE is_churn) / count(DISTINCT msno), 2) AS churn_pct
FROM cohort
GROUP BY target_month
ORDER BY target_month;
