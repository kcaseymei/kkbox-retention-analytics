-- Row counts of the staged sources must equal the full-data audit (notebooks/01_data_audit.ipynb).
-- Returns the sources whose count differs.
with actual as (
    select 'members' as source, count(*) as n from {{ ref('stg_members') }}
    union all select 'official labels v1', count(*) from {{ ref('stg_official_labels') }} where release = 'v1'
    union all select 'official labels v2', count(*) from {{ ref('stg_official_labels') }} where release = 'v2'
    union all select 'transactions v1', count(*) from {{ ref('stg_transactions') }} where release = 'v1'
    union all select 'transactions v2', count(*) from {{ ref('stg_transactions') }} where release = 'v2'
),
expected as (
    select * from (values
        ('members', 6769473), ('official labels v1', 992931), ('official labels v2', 970960),
        ('transactions v1', 21547746), ('transactions v2', 1431009)) as t(source, n)
)
select a.source, a.n as actual_rows, e.n as audit_rows
from actual a join expected e using (source)
where a.n <> e.n
