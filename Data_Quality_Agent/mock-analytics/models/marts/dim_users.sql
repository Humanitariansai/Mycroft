{{ config(materialized='table') }}

-- One row per user, enriched with their account portfolio.
-- Pulls signup_at from stg_users (which renames signup_date upstream),
-- so this mart breaks transitively when Scenario 1 fires.

with users as (
    select
        user_id,
        email,
        full_name,
        country,
        is_active,
        signup_at
    from {{ ref('stg_users') }}
),

accounts as (
    select
        owner_user_id,
        count(*)                                as account_count,
        max(plan_tier)                          as highest_plan_tier,
        min(account_created_at)                 as first_account_at
    from {{ ref('stg_accounts') }}
    group by owner_user_id
),

subs as (
    select
        a.owner_user_id,
        count(*) filter (where s.subscription_status = 'active')        as active_subscription_count,
        count(*) filter (where s.subscription_status = 'cancelled')     as cancelled_subscription_count
    from {{ ref('stg_subscriptions') }} s
    inner join {{ ref('stg_accounts') }} a using (account_id)
    group by a.owner_user_id
)

select
    u.user_id,
    u.email,
    u.full_name,
    u.country,
    u.is_active,
    u.signup_at,
    coalesce(a.account_count, 0)                            as account_count,
    a.highest_plan_tier,
    a.first_account_at,
    coalesce(s.active_subscription_count, 0)                as active_subscription_count,
    coalesce(s.cancelled_subscription_count, 0)             as cancelled_subscription_count
from users u
left join accounts a on a.owner_user_id = u.user_id
left join subs s on s.owner_user_id = u.user_id
