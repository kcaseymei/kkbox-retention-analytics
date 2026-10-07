-- Question: what does one user's subscription history look like (grain: one row per transaction)?
-- Use: sanity-check that the expiration date moves forward with each renewal.
-- The user is picked deterministically (first msno in order with exactly 12 transactions in release v1); msno is not selected, so no identifier is shown.
SELECT transaction_date, membership_expire_date, payment_plan_days, is_cancel
FROM analytics.transactions
WHERE release = 'v1' AND msno = (SELECT msno FROM analytics.transactions WHERE release = 'v1'
              GROUP BY msno HAVING count(*) = 12 ORDER BY msno LIMIT 1)
ORDER BY transaction_date, membership_expire_date;
