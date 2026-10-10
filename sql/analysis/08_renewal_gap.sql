-- Question: how long after an expiration does the next transaction happen (the renewal gap)?
-- Grain: one row per non-cancel transaction whose expiration is 2015-02-01..2017-01-31 (at least 59 days
-- of follow-up remain, data ends 2017-03-31). Gap = next transaction date - expiration date; a negative
-- gap is an early renewal. The churn rule treats 30+ days (or no later transaction) as churn.
WITH tx AS (
    SELECT msno, membership_expire_date,
           lead(transaction_date) OVER (PARTITION BY msno
                                        ORDER BY transaction_date, membership_expire_date) AS next_tx_date
    FROM analytics.transactions
    WHERE is_cancel = 0),
gaps AS (
    SELECT next_tx_date - membership_expire_date AS gap_days
    FROM tx
    WHERE membership_expire_date BETWEEN '2015-02-01' AND '2017-01-31')
SELECT CASE WHEN gap_days IS NULL THEN '7 no later transaction'
            WHEN gap_days < 0   THEN '1 early (before expiry)'
            WHEN gap_days = 0   THEN '2 on expiry day'
            WHEN gap_days <= 7  THEN '3 1-7 days'
            WHEN gap_days <= 14 THEN '4 8-14 days'
            WHEN gap_days <= 29 THEN '5 15-29 days'
            ELSE '6 30+ days (churn rule)' END AS gap_band,
       count(*) AS expirations,
       round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS share_pct
FROM gaps
GROUP BY 1
ORDER BY 1;
