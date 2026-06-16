{{ config(materialized='view') }}

-- Thin pass-through of the operational users table.
-- Trap: this model references `signup_date` by name. Scenario 1's PR renames
-- the source column to `created_at`; this select-list breaks at dbt compile.

with source as (
    select * from {{ source('app_service', 'users') }}
)

select
    id              as user_id,
    email,
    full_name,
    country,
    is_active,
    signup_date     as signup_at
from source
