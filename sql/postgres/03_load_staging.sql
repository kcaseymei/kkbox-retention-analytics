-- Load the raw CSV files into staging. Run with psql from the repository root (paths are relative).
\echo Loading label files
\copy staging.train_v1 FROM 'data/raw/train.csv' WITH (FORMAT csv, HEADER true)
\copy staging.train_v2 FROM 'data/raw/train_v2.csv' WITH (FORMAT csv, HEADER true)
\echo Loading members
\copy staging.members_v3 FROM 'data/raw/members_v3.csv' WITH (FORMAT csv, HEADER true)
\echo Loading transactions (about 23 million rows)
\copy staging.transactions_v1 FROM 'data/raw/transactions.csv' WITH (FORMAT csv, HEADER true)
\copy staging.transactions_v2 FROM 'data/raw/transactions_v2.csv' WITH (FORMAT csv, HEADER true)
