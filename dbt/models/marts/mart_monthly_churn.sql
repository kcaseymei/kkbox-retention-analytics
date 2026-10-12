-- Grain: one row per target month. Churn label rate within the labeled population of the month (not a
-- platform churn rate). Rebuilt labels for 2015-07 to 2017-02; 2017-03 uses the official labels, so its
-- population and label definition differ (docs/churn_definition.md).
select
    target_month,
    label_source,
    split_role,
    count(*)                                                        as users,
    sum(is_churn)                                                   as churners,
    round(100.0 * avg(is_churn), 2)                                 as churn_rate_pct,
    round(100.0 * avg(case when no_log_90_flag then 1 else 0 end), 2) as no_listening_90_days_pct,
    round(100.0 * avg(case when last_auto_renew = 0 then 1 else 0 end), 2) as auto_renew_off_pct,
    round(100.0 * avg(is_churn) filter (where last_auto_renew = 0), 2) as churn_rate_auto_renew_off_pct,
    round(100.0 * avg(is_churn) filter (where last_auto_renew = 1), 2) as churn_rate_auto_renew_on_pct
from {{ ref('mart_user_month_features') }}
group by target_month, label_source, split_role
