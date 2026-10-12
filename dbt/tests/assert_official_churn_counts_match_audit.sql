-- Number of churn labels in the official files must equal the audit (63,471 and 87,330).
select release, sum(is_churn) as churners
from {{ ref('stg_official_labels') }}
group by release
having (release = 'v1' and sum(is_churn) <> 63471) or (release = 'v2' and sum(is_churn) <> 87330)
