select target_month, churn_rate_pct
from {{ ref('mart_monthly_churn') }}
where churn_rate_pct < 0 or churn_rate_pct > 100 or churners > users
