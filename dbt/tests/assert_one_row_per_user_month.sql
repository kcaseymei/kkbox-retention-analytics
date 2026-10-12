-- Grain of the feature mart: one row per user and target month.
select msno, target_month, count(*) as n
from {{ ref('mart_user_month_features') }}
group by msno, target_month
having count(*) > 1
