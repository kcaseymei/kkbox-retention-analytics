-- Grain: one row per user and official label file. These are training label files, not the competition test set.
select 'v1' as release, '2017-02' as target_month, msno, try_cast(is_churn as smallint) as is_churn
from {{ source('raw', 'train_v1') }}
union all
select 'v2' as release, '2017-03' as target_month, msno, try_cast(is_churn as smallint) as is_churn
from {{ source('raw', 'train_v2') }}
