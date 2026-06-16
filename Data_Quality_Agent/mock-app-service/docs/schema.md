# Schema

Operational schema for `mock-app-service`. Five tables, three "trap" columns whose names and units are load-bearing for the demo scenarios.

## Enum types

```sql
CREATE TYPE subscription_status AS ENUM ('active', 'trialing', 'cancelled');
-- Scenario 3 adds 'paused' via ALTER TYPE ... ADD VALUE.

CREATE TYPE billing_interval AS ENUM ('monthly', 'yearly');

CREATE TYPE transaction_status AS ENUM ('succeeded', 'failed', 'refunded');
```

## Tables

### `users`

| Column        | Type                       | Notes |
|---------------|----------------------------|-------|
| `id`          | `BIGINT PRIMARY KEY`       | autoincrement |
| `email`       | `VARCHAR(320) UNIQUE NOT NULL` | indexed |
| `full_name`   | `VARCHAR(200)`             | |
| `country`     | `VARCHAR(2)`               | ISO-2 code, indexed (for `dim_users`) |
| `is_active`   | `BOOLEAN NOT NULL`         | default true |
| **`signup_date`** | `TIMESTAMPTZ NOT NULL` | **Scenario 1 trap:** renamed to `created_at` |

Consumed by `stg_users` → `dim_users`, `fct_engagement`.

### `accounts`

| Column          | Type | Notes |
|-----------------|------|-------|
| `id`            | `BIGINT PRIMARY KEY` | |
| `owner_user_id` | `BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE` | |
| `name`          | `VARCHAR(200) NOT NULL` | |
| `plan_tier`     | `VARCHAR(20) NOT NULL DEFAULT 'free'` | one of `free`, `pro`, `team`, `enterprise` |
| `created_at`    | `TIMESTAMPTZ NOT NULL` | |

Consumed by `stg_accounts` → `dim_users`, `fct_revenue`.

### `subscriptions`

| Column             | Type | Notes |
|--------------------|------|-------|
| `id`               | `BIGINT PRIMARY KEY` | |
| `account_id`       | `BIGINT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE` | |
| `plan_name`        | `VARCHAR(50) NOT NULL` | e.g. `pro_monthly` |
| **`amount_cents`** | `BIGINT NOT NULL` | **Scenario 2 trap:** renamed to `amount`, type → `NUMERIC(12,2)`, backfilled `/100` |
| `currency`         | `VARCHAR(3) NOT NULL DEFAULT 'USD'` | |
| `billing_interval` | `billing_interval NOT NULL` | monthly or yearly |
| **`status`**       | `subscription_status NOT NULL` | **Scenario 3 trap:** missing `paused` |
| `started_at`       | `TIMESTAMPTZ NOT NULL` | |
| `canceled_at`      | `TIMESTAMPTZ` | nullable |

Consumed by `stg_subscriptions` → `fct_mrr`, `fct_revenue`.

### `transactions`

| Column            | Type | Notes |
|-------------------|------|-------|
| `id`              | `BIGINT PRIMARY KEY` | |
| `account_id`      | `BIGINT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE` | |
| `subscription_id` | `BIGINT REFERENCES subscriptions(id) ON DELETE SET NULL` | |
| `amount_cents`    | `BIGINT NOT NULL` | |
| `currency`        | `VARCHAR(3) NOT NULL` | |
| `status`          | `transaction_status NOT NULL` | |
| `occurred_at`     | `TIMESTAMPTZ NOT NULL` | indexed |

Consumed by `stg_transactions` → `fct_revenue`.

### `events`

| Column        | Type | Notes |
|---------------|------|-------|
| `id`          | `BIGINT PRIMARY KEY` | |
| `user_id`     | `BIGINT REFERENCES users(id) ON DELETE SET NULL` | |
| `account_id`  | `BIGINT REFERENCES accounts(id) ON DELETE SET NULL` | |
| `event_name`  | `VARCHAR(80) NOT NULL` | indexed |
| `occurred_at` | `TIMESTAMPTZ NOT NULL` | indexed |
| `properties`  | `JSONB` | |

Consumed by `stg_events` → `fct_engagement`.

## The three planted columns, in one line

1. `users.signup_date` — the name itself is the trap (Scenario 1 rename).
2. `subscriptions.amount_cents` — the unit suffix is the trap (Scenario 2 rename + retype + backfill).
3. `subscription_status` enum without `paused` — the missing value is the trap (Scenario 3 enum expansion).
