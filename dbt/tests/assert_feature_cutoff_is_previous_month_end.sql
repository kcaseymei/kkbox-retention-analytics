-- Leakage control: the cutoff of every row must be the last day of the month before the target month.
select target_month, cutoff
from {{ ref('mart_user_month_features') }}
where cutoff <> strftime((strptime(target_month || '-01', '%Y-%m-%d')::date - interval 1 day), '%Y%m%d')
limit 100
