-- Question: of the users whose first transaction in the data is in month C, what share has an active
-- subscription at the end of month C+k, for k = 0..6?
-- Active at date d = a non-cancel transaction with transaction_date <= d <= membership_expire_date.
-- Cohorts: first transaction 2016-01 to 2016-06 (the data ends 2017-02, so k = 6 is observable).
-- Caveats: the data starts on 2015-01-01, so "first transaction" can be a returning user, not a new one;
-- the share can rise again when users who lapsed come back (reactivation).
WITH first_tx AS (
    SELECT msno, date_trunc('month', min(transaction_date))::date AS cohort_month
    FROM analytics.transactions
    WHERE is_cancel = 0
    GROUP BY msno
    HAVING date_trunc('month', min(transaction_date)) BETWEEN '2016-01-01' AND '2016-06-01'),
cohort_size AS (
    SELECT cohort_month, count(*) AS cohort_users FROM first_tx GROUP BY cohort_month),
active AS (   -- one row per user and month offset at which the user is active
    SELECT f.cohort_month, k, f.msno
    FROM first_tx f
    CROSS JOIN generate_series(0, 6) AS k
    JOIN analytics.transactions t ON t.msno = f.msno AND t.is_cancel = 0
    WHERE t.transaction_date <= (f.cohort_month + (k + 1) * interval '1 month' - interval '1 day')::date
      AND t.membership_expire_date >= (f.cohort_month + (k + 1) * interval '1 month' - interval '1 day')::date
    GROUP BY f.cohort_month, k, f.msno),
counts AS (
    SELECT cohort_month, k, count(*) AS active_users FROM active GROUP BY cohort_month, k)
SELECT to_char(s.cohort_month, 'YYYY-MM') AS cohort, s.cohort_users,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 0) / s.cohort_users, 1) AS m0,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 1) / s.cohort_users, 1) AS m1,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 2) / s.cohort_users, 1) AS m2,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 3) / s.cohort_users, 1) AS m3,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 4) / s.cohort_users, 1) AS m4,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 5) / s.cohort_users, 1) AS m5,
       round(100.0 * max(c.active_users) FILTER (WHERE c.k = 6) / s.cohort_users, 1) AS m6
FROM cohort_size s JOIN counts c USING (cohort_month)
GROUP BY s.cohort_month, s.cohort_users
ORDER BY s.cohort_month;
