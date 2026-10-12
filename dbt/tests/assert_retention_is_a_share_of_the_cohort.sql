-- Retention cannot exceed the cohort, and offset 0 starts near 100%.
select cohort_month, first_plan_group, month_offset, active_users, cohort_users
from {{ ref('mart_cohort_retention') }}
where active_users > cohort_users or retention_pct < 0 or retention_pct > 100
