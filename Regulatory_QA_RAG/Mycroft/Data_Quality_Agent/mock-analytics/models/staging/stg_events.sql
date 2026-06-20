{{ config(materialized='view') }}

with source as (
    select * from {{ source('app_service', 'events') }}
)

select
    id              as event_id,
    user_id,
    account_id,
    event_name,
    occurred_at
from source
