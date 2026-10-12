-- Leakage control (sanity): features measured at the cutoff cannot describe the future, so "days since" counts,
-- tenure, and registration age must not be negative. A negative value would mean a source row dated after the cutoff.
select msno, target_month
from {{ ref('mart_user_month_features') }}
where days_since_last_log < 0
   or days_since_last_transaction < 0
   or tenure_days < 0
   or registration_days < 0
limit 100
