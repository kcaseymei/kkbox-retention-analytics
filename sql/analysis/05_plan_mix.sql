-- Question: how are transactions split by plan length, and how often is auto-renew on? (release v1 only)
-- Grain: one row per transaction (not per user). Plan length 0 days does not mean zero payment (DQ-011).
SELECT CASE WHEN payment_plan_days = 30 THEN '30 days'
            WHEN payment_plan_days = 0 THEN '0 days'
            WHEN payment_plan_days < 30 THEN 'under 30'
            ELSE 'over 30' END AS plan_type,
       count(*) AS transactions,
       round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS share_pct,
       round(100.0 * avg(is_auto_renew), 2) AS auto_renew_pct
FROM analytics.transactions
WHERE release = 'v1'
GROUP BY 1
ORDER BY 2 DESC;
