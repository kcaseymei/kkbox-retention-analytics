-- Grain: one row per user and target month (key: msno, target_month). Source: the 63-column feature tables
-- built by src/build_features.py; every feature uses data dated on or before the cutoff (the last day of the
-- previous month). Label: rebuilt for 2015-07 to 2017-02, official for 2017-03 (see label_source).
select
    f.*,
    case
        when f.days_to_expiration between 1 and 7   then '1-7'
        when f.days_to_expiration between 8 and 14  then '8-14'
        when f.days_to_expiration between 15 and 21 then '15-21'
        when f.days_to_expiration between 22 and 31 then '22-31'
        else 'outside 1-31'
    end as lead_time_band,
    case
        when f.target_month between '2016-07' and '2016-12' then 'validation'
        when f.target_month in ('2017-01', '2017-02')       then 'test'
        when f.target_month = '2017-03'                     then 'external'
        else 'training'
    end as split_role
from {{ source('raw', 'monthly_features') }} as f
