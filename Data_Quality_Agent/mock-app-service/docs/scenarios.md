# Demo Scenarios

Each scenario is a drafted PR against `mock-app-service`. The PR description in each is intended to read like a real engineer wrote it — Scenario 2's in particular should look like routine cleanup, because the entire point is that a human reviewer would miss the unit shift.

These are **drafts**. They are not committed against the baseline schema until Phase 2 inputs are needed.

---

## Scenario 1 — Structural break: rename `signup_date` → `created_at`

**Branch:** `rename-signup-date`

**PR title:** Rename `users.signup_date` to `created_at` for consistency

**PR description:**
> Every other table on `users` uses `created_at` for the row's creation timestamp; `signup_date` is the odd one out. This PR renames the column and updates ORM + API references.

### Migration

```python
"""rename users.signup_date to created_at

Revision ID: 0002_rename_signup_date
Revises: 0001_initial
"""
from alembic import op

revision = "0002_rename_signup_date"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "signup_date", new_column_name="created_at")


def downgrade() -> None:
    op.alter_column("users", "created_at", new_column_name="signup_date")
```

### Model change

`app/models/users.py`:

```diff
-    signup_date: Mapped[datetime] = mapped_column(
+    created_at: Mapped[datetime] = mapped_column(
         DateTime(timezone=True),
         nullable=False,
         server_default=func.now(),
     )
```

### Expected downstream effect

`stg_users.sql` in `mock-analytics` selects `signup_date`. After this migration:

```
Compilation Error in model stg_users (models/staging/stg_users.sql)
  Column 'signup_date' does not exist on relation 'users'
```

The deterministic layer catches this from the manifest alone — it's a column rename in a model whose lineage includes `users.signup_date`.

---

## Scenario 2 — Semantic unit break: `amount_cents` → `amount`

**Branch:** `standardize-amount-column`

**PR title:** Standardize amount column for new pricing tables

**PR description:**
> Going forward we'd like the canonical money column on `subscriptions` to be `amount` (NUMERIC(12,2)) rather than `amount_cents` (BIGINT). Aligns with the format of the upcoming `pricing_plans` and `invoice_line_items` tables and saves a `/100` conversion on the API side. Backfills existing rows.

### Migration

```python
"""standardize subscriptions.amount column

Revision ID: 0003_subscriptions_amount
Revises: 0001_initial
"""
import sqlalchemy as sa
from alembic import op

revision = "0003_subscriptions_amount"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
    )
    op.execute("UPDATE subscriptions SET amount = amount_cents / 100.0")
    op.alter_column("subscriptions", "amount", nullable=False)
    op.drop_column("subscriptions", "amount_cents")


def downgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("amount_cents", sa.BigInteger(), nullable=True),
    )
    op.execute("UPDATE subscriptions SET amount_cents = (amount * 100)::bigint")
    op.alter_column("subscriptions", "amount_cents", nullable=False)
    op.drop_column("subscriptions", "amount")
```

### Model change

`app/models/subscriptions.py`:

```diff
-    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
+    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
```

### Expected downstream effect

`stg_subscriptions.sql` originally does:

```sql
amount_cents / 100.0 AS amount_usd
```

A naive fix is to rename the column reference: `amount / 100.0 AS amount_usd`. But the new `amount` is **already in dollars**, so dividing by 100 makes it 100x too small. `fct_mrr` will return a number that looks vaguely right (no zero, no crash) but is off by two orders of magnitude.

This is the showpiece scenario. The deterministic layer cannot catch it. The LLM should flag the unit suffix change (`_cents` removed) + the backfill `amount = amount_cents / 100.0` + the unchanged division in `stg_subscriptions` as a unit-of-measure regression.

---

## Scenario 3 — Enum expansion: add `paused` to `subscription_status`

**Branch:** `add-paused-subscription-status`

**PR title:** Add `paused` to `subscription_status` enum

**PR description:**
> Billing wants to support a "paused" state for subscriptions that are temporarily inactive without being cancelled (e.g., customer-requested holds, dunning pauses). Adds the enum value and a follow-up PR will surface it in the admin UI.

### Migration

```python
"""add paused to subscription_status

Revision ID: 0004_subscription_status_paused
Revises: 0001_initial
"""
from alembic import op

revision = "0004_subscription_status_paused"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block in Postgres < 12.
    # On recent versions it's fine; setting autocommit_block defensively.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE subscription_status ADD VALUE IF NOT EXISTS 'paused'")


def downgrade() -> None:
    # Postgres does not support removing enum values. Recreate the type if a true
    # downgrade is needed (omitted here — this migration is effectively forward-only).
    pass
```

### Model change

`app/models/subscriptions.py`:

```diff
 class SubscriptionStatus(str, enum.Enum):
     active = "active"
     trialing = "trialing"
     cancelled = "cancelled"
+    paused = "paused"
```

### Expected downstream effect

`fct_mrr.sql` filters:

```sql
WHERE status IN ('active', 'trialing')
```

Paused subscriptions silently drop out of MRR. The model compiles, runs, returns a number, and is wrong in a way no manifest-only check can detect — the filter pattern in `fct_mrr` is the trap, and you need to *read* the migration's added value and the downstream filter to know whether `paused` belongs in MRR.

The deterministic layer can at best surface a pattern: "an enum value was added; here are the SQL files that hard-code values from this enum." The LLM is what decides whether that's a problem.
