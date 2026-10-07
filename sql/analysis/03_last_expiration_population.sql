-- Question: how many users have their LAST expiration (at the 2017-01-31 cutoff) in February 2017?
-- Simplified rule: latest transaction by date, then by expiration date. The Python rebuild
-- (src/churn_labels.py) also orders by plan signature and cancellations and finds 879,537 users;
-- the difference is a check on that detail, not an error in either.
WITH last_tx AS (
    SELECT msno, membership_expire_date,
           row_number() OVER (PARTITION BY msno
                              ORDER BY transaction_date DESC, membership_expire_date DESC) AS rn
    FROM analytics.transactions
    WHERE transaction_date <= '2017-01-31')
SELECT count(*) AS feb_2017_population
FROM last_tx
WHERE rn = 1
  AND membership_expire_date BETWEEN '2017-02-01' AND '2017-02-28';
