{{ config(materialized='view') }}

with source as (
    select * from {{ source('app_service', 'transactions') }}
)

select
    id                          as transaction_id,
    account_id,
    subscription_id,
    amount_cents / 100.0        as amount_usd,
    currency,
    status                      as transaction_status,
    occurred_at
from source
