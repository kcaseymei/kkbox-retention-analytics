-- Question: churn label rate in the two official label files, and how many users lack a member profile.
-- Population: users in the official files (not platform churn). Left join keeps users without a profile.
SELECT l.release, l.target_month,
       count(*) AS users,
       round(100.0 * avg(l.is_churn), 2) AS churn_pct,
       round(100.0 * avg((m.msno IS NULL)::int), 2) AS no_profile_pct
FROM analytics.official_labels l
LEFT JOIN analytics.members m USING (msno)
GROUP BY 1, 2
ORDER BY 1;
