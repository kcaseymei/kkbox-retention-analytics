-- Staging tables: one per source file, every column as text so no value is altered on load.
DROP TABLE IF EXISTS staging.train_v1, staging.train_v2, staging.members_v3,
                     staging.transactions_v1, staging.transactions_v2;

CREATE TABLE staging.train_v1 (msno text, is_churn text);   -- train.csv
CREATE TABLE staging.train_v2 (msno text, is_churn text);   -- train_v2.csv

CREATE TABLE staging.members_v3 (                           -- members_v3.csv
    msno text, city text, bd text, gender text, registered_via text, registration_init_time text);

CREATE TABLE staging.transactions_v1 (                      -- transactions.csv
    msno text, payment_method_id text, payment_plan_days text, plan_list_price text,
    actual_amount_paid text, is_auto_renew text, transaction_date text,
    membership_expire_date text, is_cancel text);
CREATE TABLE staging.transactions_v2 (LIKE staging.transactions_v1);   -- transactions_v2.csv
