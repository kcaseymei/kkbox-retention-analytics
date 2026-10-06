-- Typed analytics tables built from staging. Source values are only cast, never cleaned:
-- anomalies found in the audit (see reports/data_quality_issues.md) are kept and flagged later.
DROP TABLE IF EXISTS analytics.transactions, analytics.official_labels, analytics.members;

CREATE TABLE analytics.members (
    msno             text PRIMARY KEY,
    city             smallint NOT NULL,           -- category code, meaning unknown
    bd               integer  NOT NULL,           -- age as supplied: -7168..2016, 0 for 67% (DQ-003)
    gender           text CHECK (gender IN ('male', 'female')),   -- NULL for 65% (DQ-002)
    registered_via   smallint NOT NULL,           -- category code, meaning unknown
    registration_date date    NOT NULL);
INSERT INTO analytics.members
SELECT msno, city::smallint, bd::integer, gender, registered_via::smallint,
       to_date(registration_init_time, 'YYYYMMDD')
FROM staging.members_v3;

-- The two supplied label files, one row per user and file. target_month is the documented expiration
-- month (February and March 2017), checked against the transactions in notebooks/02_population_and_churn.ipynb.
CREATE TABLE analytics.official_labels (
    release      text NOT NULL CHECK (release IN ('v1', 'v2')),
    target_month text NOT NULL,
    msno         text NOT NULL,
    is_churn     smallint NOT NULL CHECK (is_churn IN (0, 1)),
    PRIMARY KEY (release, msno));
INSERT INTO analytics.official_labels
SELECT 'v1', '2017-02', msno, is_churn::smallint FROM staging.train_v1
UNION ALL
SELECT 'v2', '2017-03', msno, is_churn::smallint FROM staging.train_v2;

-- Both transaction releases stacked with a release column. No natural key exists
-- ((msno, transaction_date) repeats), so a surrogate key identifies a row.
CREATE TABLE analytics.transactions (
    tx_id                  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    release                text     NOT NULL CHECK (release IN ('v1', 'v2')),
    msno                   text     NOT NULL,
    payment_method_id      smallint NOT NULL,
    payment_plan_days      smallint NOT NULL,     -- 0..450; 0 does not mean zero payment (DQ-011)
    plan_list_price        integer  NOT NULL,     -- New Taiwan Dollar
    actual_amount_paid     integer  NOT NULL,     -- New Taiwan Dollar
    is_auto_renew          smallint NOT NULL CHECK (is_auto_renew IN (0, 1)),
    transaction_date       date     NOT NULL,
    membership_expire_date date     NOT NULL,     -- includes 1970-01-01 and dates up to 2036 (DQ-009, DQ-010)
    is_cancel              smallint NOT NULL CHECK (is_cancel IN (0, 1)));
INSERT INTO analytics.transactions
    (release, msno, payment_method_id, payment_plan_days, plan_list_price, actual_amount_paid,
     is_auto_renew, transaction_date, membership_expire_date, is_cancel)
SELECT 'v1', msno, payment_method_id::smallint, payment_plan_days::smallint, plan_list_price::integer,
       actual_amount_paid::integer, is_auto_renew::smallint, to_date(transaction_date, 'YYYYMMDD'),
       to_date(membership_expire_date, 'YYYYMMDD'), is_cancel::smallint
FROM staging.transactions_v1
UNION ALL
SELECT 'v2', msno, payment_method_id::smallint, payment_plan_days::smallint, plan_list_price::integer,
       actual_amount_paid::integer, is_auto_renew::smallint, to_date(transaction_date, 'YYYYMMDD'),
       to_date(membership_expire_date, 'YYYYMMDD'), is_cancel::smallint
FROM staging.transactions_v2;

CREATE INDEX transactions_user_date_idx ON analytics.transactions (msno, transaction_date);
CREATE INDEX transactions_expire_idx    ON analytics.transactions (membership_expire_date);
ANALYZE analytics.members;
ANALYZE analytics.official_labels;
ANALYZE analytics.transactions;
