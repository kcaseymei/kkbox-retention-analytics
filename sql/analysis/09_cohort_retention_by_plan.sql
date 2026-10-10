-- Question: does retention after the first transaction depend on the plan length of that first transaction?
-- Same definition as 07 (cohorts 2016-01..2016-06 pooled, active at the end of month C+k), split by the
-- plan length of the user's first non-cancel transaction.
-- Caveat: "first transaction" can be a returning user (data starts 2015-01-01).
WITH ranked AS (
    SELECT msno, payment_plan_days, transaction_date,
           row_number() OVER (PARTITION BY msno ORDER BY transaction_date, membership_expire_date) AS rn
    FROM analytics.transactions
    WHERE is_cancel = 0),
first_tx AS (
    SELECT msno, date_trunc('month', transaction_date)::date AS cohort_month,
           CASE WHEN payment_plan_days = 30 THEN '30 days'
                WHEN payment_plan_days = 0 THEN '0 days'
                WHEN payment_plan_days < 30 THEN 'under 30 days'
                ELSE 'over 30 days' END AS first_plan
    FROM ranked
    WHERE rn = 1 AND date_trunc('month', transaction_date) BETWEEN '2016-01-01' AND '2016-06-01'),
plan_size AS (
    SELECT first_plan, count(*) AS cohort_users FROM first_tx GROUP BY first_plan),
active AS (
    SELECT f.first_plan, k, f.msno
    FROM first_tx f
    CROSS JOIN generate_series(0, 6) AS k
    JOIN analytics.transactions t ON t.msno = f.msno AND t.is_cancel = 0
    WHERE t.transaction_date <= (f.cohort_month + (k + 1) * interval '1 month' - interval '1 day')::date
      AND t.membership_expire_date >= (f.cohort_month + (k + 1) * interval '1 month' - interval '1 day')::date
    GROUP BY f.first_plan, k, f.msno),
counts AS (
    SELECT first_plan, k, count(*) AS active_users FROM active GROUP BY first_plan, k)
SELECT s.first_plan, s.cohort_users,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 0) / s.cohort_users, 1) AS m0,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 1) / s.cohort_users, 1) AS m1,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 2) / s.cohort_users, 1) AS m2,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 3) / s.cohort_users, 1) AS m3,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 4) / s.cohort_users, 1) AS m4,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 5) / s.cohort_users, 1) AS m5,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 6) / s.cohort_users, 1) AS m6
FROM plan_size s JOIN counts c USING (first_plan)
GROUP BY s.first_plan, s.cohort_users
ORDER BY s.cohort_users DESC;
