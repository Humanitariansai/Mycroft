{{ config(materialized='table') }}

-- Per-user engagement summary. Sources: events + users.

with events as (
    select
        event_id,
        user_id,
        event_name,
        occurred_at
    from {{ ref('stg_events') }}
    where user_id is not null
),

users as (
    select
        user_id,
        country,
        signup_at
    from {{ ref('stg_users') }}
),

per_user as (
    select
        user_id,
        count(*)                                                                    as event_count,
        count(distinct event_name)                                                  as distinct_event_count,
        count(*) filter (where event_name = 'login')                                as login_count,
        count(*) filter (where event_name = 'feature_used')                         as feature_used_count,
        min(occurred_at)                                                            as first_event_at,
        max(occurred_at)                                                            as last_event_at
    from events
    group by user_id
)

select
    u.user_id,
    u.country,
    u.signup_at,
    coalesce(p.event_count, 0)                                                      as event_count,
    coalesce(p.distinct_event_count, 0)                                             as distinct_event_count,
    coalesce(p.login_count, 0)                                                      as login_count,
    coalesce(p.feature_used_count, 0)                                               as feature_used_count,
    p.first_event_at,
    p.last_event_at,
    date_diff('day', u.signup_at, p.last_event_at)                                  as days_active
from users u
left join per_user p using (user_id)
