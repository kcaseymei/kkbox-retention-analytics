-- Grain: one row per cohort month (first non-cancellation transaction in the data), first plan group, and month
-- offset k. Retention = users with an active subscription at the end of month C+k / cohort users.
-- Active at date d = a non-cancellation transaction with transaction_date <= d <= membership_expire_date.
-- Cohorts 2016-01 to 2016-06 (the data ends 2017-02, so k = 6 is observable). Caveat: the data starts on
-- 2015-01-01, so "first transaction" can be a returning user; retention can rise when lapsed users return.
with ranked as (
    select
        msno, payment_plan_days, transaction_date,
        row_number() over (
            partition by msno
            order by transaction_date, membership_expire_date, payment_plan_days, plan_list_price, payment_method_id
        ) as rn
    from {{ ref('stg_transactions') }}
    where is_cancel = 0
),
first_tx as (
    select
        msno,
        date_trunc('month', transaction_date)::date as cohort_month,
        case
            when payment_plan_days = 30 then '30 days'
            when payment_plan_days = 0  then '0 days'
            when payment_plan_days < 30 then 'under 30 days'
            else 'over 30 days'
        end as first_plan_group
    from ranked
    where rn = 1
      and date_trunc('month', transaction_date) between date '2016-01-01' and date '2016-06-01'
),
cohort_size as (
    select cohort_month, first_plan_group, count(*) as cohort_users from first_tx group by all
),
active as (
    select f.cohort_month, f.first_plan_group, k.k as month_offset, f.msno
    from first_tx f
    cross join (select unnest(range(0, 7)) as k) k
    join {{ ref('stg_transactions') }} t on t.msno = f.msno and t.is_cancel = 0
    where t.transaction_date <= (f.cohort_month + (k.k + 1) * interval 1 month - interval 1 day)
      and t.membership_expire_date >= (f.cohort_month + (k.k + 1) * interval 1 month - interval 1 day)
    group by all
),
active_counts as (
    select cohort_month, first_plan_group, month_offset, count(*) as active_users from active group by all
)
select
    c.cohort_month,
    c.first_plan_group,
    a.month_offset,
    c.cohort_users,
    a.active_users,
    round(100.0 * a.active_users / c.cohort_users, 1) as retention_pct
from cohort_size c
join active_counts a using (cohort_month, first_plan_group)
