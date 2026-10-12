-- One label per user and release.
select release, msno, count(*) as n
from {{ ref('stg_official_labels') }}
group by release, msno
having count(*) > 1
