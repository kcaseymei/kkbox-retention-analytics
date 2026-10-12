{{ config(materialized='table') }}
-- Grain: one row per transaction record, both releases stacked with a release column and no de-duplication
-- (the two releases overlap on 7,249 user-date keys; the overlap rule is an open item).
{% for release, table in [('v1', 'transactions_v1'), ('v2', 'transactions_v2')] %}
select
    '{{ release }}'                                              as release,
    msno,
    try_cast(payment_method_id as smallint)                      as payment_method_id,
    try_cast(payment_plan_days as smallint)                      as payment_plan_days,
    try_cast(plan_list_price as integer)                         as plan_list_price,
    try_cast(actual_amount_paid as integer)                      as actual_amount_paid,
    try_cast(is_auto_renew as smallint)                          as is_auto_renew,
    strptime(transaction_date, '%Y%m%d')::date                   as transaction_date,
    strptime(membership_expire_date, '%Y%m%d')::date             as membership_expire_date,
    try_cast(is_cancel as smallint)                              as is_cancel
from {{ source('raw', table) }}
{% if not loop.last %}union all{% endif %}
{% endfor %}
