-- Grain: one row per member. Source values are only cast, never cleaned: anomalies (age 0, missing gender)
-- are kept and flagged downstream (see reports/data_quality_issues.md).
select
    msno,
    try_cast(city as smallint)                         as city,
    try_cast(bd as integer)                            as bd,
    nullif(gender, '')                                 as gender,
    try_cast(registered_via as smallint)               as registered_via,
    strptime(registration_init_time, '%Y%m%d')::date   as registration_date
from {{ source('raw', 'members') }}
