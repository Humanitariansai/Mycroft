{{ config(materialized='table') }}

-- Recognized revenue from completed transactions, rolled up to month + account.
-- Joins three staging models so the manifest captures non-trivial column-level
-- lineage: transactions, subscriptions (for plan context), accounts (for tier).

with tx as (
    select
        transaction_id,
        account_id,
        subscription_id,
        amount_usd,
        transaction_status,
        occurred_at
    from {{ ref('stg_transactions') }}
    where transaction_status = 'succeeded'
),

subs as (
    select
        subscription_id,
        plan_name,
        billing_interval
    from {{ ref('stg_subscriptions') }}
),

accounts as (
    select
        account_id,
        plan_tier,
        owner_user_id
    from {{ ref('stg_accounts') }}
),

tx_enriched as (
    select
        t.transaction_id,
        t.account_id,
        a.owner_user_id,
        a.plan_tier,
        t.subscription_id,
        s.plan_name,
        s.billing_interval,
        date_trunc('month', t.occurred_at)              as revenue_month,
        t.amount_usd
    from tx t
    inner join accounts a using (account_id)
    left join subs s using (subscription_id)
)

select
    revenue_month,
    account_id,
    owner_user_id,
    plan_tier,
    plan_name,
    billing_interval,
    count(*)                            as transaction_count,
    sum(amount_usd)                     as revenue_usd
from tx_enriched
group by 1, 2, 3, 4, 5, 6
