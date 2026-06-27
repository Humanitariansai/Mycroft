{{ config(materialized='view') }}

with source as (
    select * from {{ source('app_service', 'accounts') }}
)

select
    id              as account_id,
    owner_user_id,
    name            as account_name,
    plan_tier,
    created_at      as account_created_at
from source
