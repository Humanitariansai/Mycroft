{{ config(materialized='view') }}

-- Trap (Scenario 2): the cents → dollars conversion lives here, as a divide
-- by 100. If the operational schema flips `amount_cents` (BIGINT, cents) to
-- `amount` (NUMERIC, dollars) and this model is naively renamed without
-- removing the division, fct_mrr ends up 100x low and every model still
-- compiles. Do NOT push the status filter down into this view -- fct_mrr's
-- explicit filter is the Scenario 3 trap and needs to stay visible there.

with source as (
    select * from {{ source('app_service', 'subscriptions') }}
)

select
    id                          as subscription_id,
    account_id,
    plan_name,
    -- amount_cents is in cents on the operational side; convert to dollars here.
    amount_cents / 100.0        as amount_usd,
    currency,
    billing_interval,
    status                      as subscription_status,
    started_at,
    canceled_at
from source
