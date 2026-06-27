{{ config(materialized='table') }}

-- Monthly Recurring Revenue, one row per active/trialing subscription.
--
-- TRAPS:
--   1. Scenario 3 — the filter `subscription_status IN ('active', 'trialing')`
--      below is what silently drops a future `paused` status. If billing adds
--      'paused' upstream, those subscriptions disappear from MRR with no error.
--   2. Scenario 2 — amount_usd flows in from stg_subscriptions, which is doing
--      the cents → dollars conversion. If the upstream column changes from
--      `amount_cents` (cents) to `amount` (dollars) and the staging model's
--      /100 isn't removed, the number this model emits is 100x too low.
--
-- Yearly subscriptions are normalized to a monthly amount.

with subs as (
    select
        subscription_id,
        account_id,
        plan_name,
        amount_usd,
        billing_interval,
        subscription_status,
        started_at,
        canceled_at
    from {{ ref('stg_subscriptions') }}
),

accounts as (
    select
        account_id,
        plan_tier,
        owner_user_id
    from {{ ref('stg_accounts') }}
),

active_subs as (
    select *
    from subs
    where subscription_status in ('active', 'trialing')
),

mrr_rows as (
    select
        s.subscription_id,
        s.account_id,
        a.owner_user_id,
        a.plan_tier,
        s.plan_name,
        s.subscription_status,
        s.billing_interval,
        s.started_at,
        s.amount_usd                                                as raw_amount_usd,
        case
            when s.billing_interval = 'yearly' then s.amount_usd / 12.0
            else s.amount_usd
        end                                                         as monthly_amount_usd
    from active_subs s
    inner join accounts a using (account_id)
)

select
    subscription_id,
    account_id,
    owner_user_id,
    plan_tier,
    plan_name,
    subscription_status,
    billing_interval,
    started_at,
    raw_amount_usd,
    monthly_amount_usd
from mrr_rows