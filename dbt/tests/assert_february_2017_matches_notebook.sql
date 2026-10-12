-- The February 2017 population and churn label rate must reproduce notebook 02 and the model report
-- (879,537 users, 3.95%).
select target_month, users, churn_rate_pct
from {{ ref('mart_monthly_churn') }}
where target_month = '2017-02' and (users <> 879537 or abs(churn_rate_pct - 3.95) > 0.01)
