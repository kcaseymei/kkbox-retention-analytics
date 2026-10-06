-- Reconcile the PostgreSQL tables with the full-data audit (notebooks/01_data_audit.ipynb).
-- Every row must read OK; a MISMATCH means the load changed or lost data.
-- Run: psql -h localhost -U kkbox -d kkbox -f sql/quality/01_reconcile_postgres.sql

\echo 1. Row counts: staging (as loaded) and analytics (typed)
WITH expected(item, audit_rows) AS (VALUES
        ('members',            6769473),
        ('official_labels v1',  992931),
        ('official_labels v2',  970960),
        ('transactions v1',   21547746),
        ('transactions v2',    1431009)),
     staging AS (
        SELECT 'members' AS item, count(*) AS n FROM staging.members_v3
        UNION ALL SELECT 'official_labels v1', count(*) FROM staging.train_v1
        UNION ALL SELECT 'official_labels v2', count(*) FROM staging.train_v2
        UNION ALL SELECT 'transactions v1', count(*) FROM staging.transactions_v1
        UNION ALL SELECT 'transactions v2', count(*) FROM staging.transactions_v2),
     analytics AS (
        SELECT 'members' AS item, count(*) AS n FROM analytics.members
        UNION ALL SELECT 'official_labels v1', count(*) FROM analytics.official_labels WHERE release = 'v1'
        UNION ALL SELECT 'official_labels v2', count(*) FROM analytics.official_labels WHERE release = 'v2'
        UNION ALL SELECT 'transactions v1', count(*) FROM analytics.transactions WHERE release = 'v1'
        UNION ALL SELECT 'transactions v2', count(*) FROM analytics.transactions WHERE release = 'v2')
SELECT e.item, e.audit_rows, s.n AS staging_rows, a.n AS analytics_rows,
       CASE WHEN e.audit_rows = s.n AND s.n = a.n THEN 'OK' ELSE 'MISMATCH' END AS status
FROM expected e JOIN staging s USING (item) JOIN analytics a USING (item)
ORDER BY e.item;

\echo 2. Audit figures reproduced from the typed tables
WITH expected(item, audit_value) AS (VALUES
        ('distinct users in transactions v1',            2363626),
        ('distinct users in transactions v2',            1197050),
        ('churn labels in official v1',                    63471),
        ('churn labels in official v2',                    87330),
        ('members with missing gender',                  4429505),
        ('members with age 0',                           4540215),
        ('transactions v1 expiring before the transaction date', 153660),
        ('transactions v2 expiring before the transaction date',   5106),
        ('transactions v1 with zero plan days',          870124),
        ('transactions v2 with zero plan days',            2218),
        ('transactions v1 expiring before 2015',           9840),
        ('(user, date) keys present in both transaction releases', 7249)),
     actual AS (
        SELECT 'distinct users in transactions v1' AS item, count(DISTINCT msno)::bigint AS n
            FROM analytics.transactions WHERE release = 'v1'
        UNION ALL SELECT 'distinct users in transactions v2', count(DISTINCT msno) FROM analytics.transactions WHERE release = 'v2'
        UNION ALL SELECT 'churn labels in official v1', sum(is_churn) FROM analytics.official_labels WHERE release = 'v1'
        UNION ALL SELECT 'churn labels in official v2', sum(is_churn) FROM analytics.official_labels WHERE release = 'v2'
        UNION ALL SELECT 'members with missing gender', count(*) FROM analytics.members WHERE gender IS NULL
        UNION ALL SELECT 'members with age 0', count(*) FROM analytics.members WHERE bd = 0
        UNION ALL SELECT 'transactions v1 expiring before the transaction date', count(*)
            FROM analytics.transactions WHERE release = 'v1' AND membership_expire_date < transaction_date
        UNION ALL SELECT 'transactions v2 expiring before the transaction date', count(*)
            FROM analytics.transactions WHERE release = 'v2' AND membership_expire_date < transaction_date
        UNION ALL SELECT 'transactions v1 with zero plan days', count(*)
            FROM analytics.transactions WHERE release = 'v1' AND payment_plan_days = 0
        UNION ALL SELECT 'transactions v2 with zero plan days', count(*)
            FROM analytics.transactions WHERE release = 'v2' AND payment_plan_days = 0
        UNION ALL SELECT 'transactions v1 expiring before 2015', count(*)
            FROM analytics.transactions WHERE release = 'v1' AND membership_expire_date < DATE '2015-01-01'
        UNION ALL SELECT '(user, date) keys present in both transaction releases', count(*)
            FROM (SELECT DISTINCT msno, transaction_date FROM analytics.transactions WHERE release = 'v1') a
            JOIN (SELECT DISTINCT msno, transaction_date FROM analytics.transactions
                  WHERE release = 'v2' AND transaction_date < DATE '2017-03-01') b USING (msno, transaction_date))
SELECT e.item, e.audit_value, a.n AS postgres_value,
       CASE WHEN e.audit_value = a.n THEN 'OK' ELSE 'MISMATCH' END AS status
FROM expected e JOIN actual a USING (item)
ORDER BY e.item;

\echo 3. Keys and date ranges
SELECT 'members.msno is unique'              AS check_name, (count(*) = count(DISTINCT msno))::text AS result FROM analytics.members
UNION ALL SELECT 'earliest transaction date', min(transaction_date)::text FROM analytics.transactions
UNION ALL SELECT 'latest transaction date',   max(transaction_date)::text FROM analytics.transactions
UNION ALL SELECT 'earliest expiration date',  min(membership_expire_date)::text FROM analytics.transactions
UNION ALL SELECT 'latest expiration date',    max(membership_expire_date)::text FROM analytics.transactions;
