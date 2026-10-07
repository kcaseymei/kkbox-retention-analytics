-- Question: how many users have ANY subscription expiring in each month (2015-02 to 2017-02)?
-- Population: any transaction (both releases) whose expiration falls in the month. Wider than the churn
-- population, which uses only each user's LAST expiration (see 03).
SELECT date_trunc('month', membership_expire_date)::date AS expire_month,
       count(DISTINCT msno) AS expiring_users
FROM analytics.transactions
WHERE membership_expire_date BETWEEN '2015-02-01' AND '2017-02-28'
GROUP BY 1
ORDER BY 1;
