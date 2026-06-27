"""Seed mock-app-service with synthetic data using Faker.

Targets (from phase-1-plan.md):
    ~1000 users, ~800 accounts, ~1500 subscriptions (mixed statuses),
    ~50k transactions, ~200k events.

Idempotent enough for demo work: if the tables are non-empty, the script exits
without doing anything. Drop / recreate with `alembic downgrade base && alembic
upgrade head` to re-seed.
"""
from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta, timezone

from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal, engine
from app.models import (
    Account,
    BillingInterval,
    Event,
    Subscription,
    SubscriptionStatus,
    Transaction,
    TransactionStatus,
    User,
)

fake = Faker()
Faker.seed(42)
random.seed(42)

N_USERS = 1_000
N_ACCOUNTS = 800
N_SUBSCRIPTIONS_TARGET = 1_500
N_TRANSACTIONS_TARGET = 50_000
N_EVENTS_TARGET = 200_000

PLAN_TIERS = ["free", "pro", "team", "enterprise"]
PLAN_TIER_WEIGHTS = [0.50, 0.30, 0.15, 0.05]

# Plan pricing in cents. Used to populate subscriptions.amount_cents.
# fct_mrr will sum these (after monthly normalization) to produce demo MRR.
PLAN_PRICING_CENTS = {
    "pro_monthly": 2_900,
    "pro_yearly": 29_000,
    "team_monthly": 9_900,
    "team_yearly": 99_000,
    "enterprise_monthly": 49_900,
    "enterprise_yearly": 499_000,
}

STATUS_WEIGHTS = [
    (SubscriptionStatus.active, 0.65),
    (SubscriptionStatus.trialing, 0.10),
    (SubscriptionStatus.cancelled, 0.25),
]

EVENT_NAMES = [
    "page_view",
    "login",
    "logout",
    "feature_used",
    "signup",
    "upgrade_clicked",
    "invite_sent",
    "export_csv",
]

NOW = datetime.now(timezone.utc)
START = NOW - timedelta(days=730)  # 2-year history


def weighted_choice(pairs: list[tuple]) -> object:
    values, weights = zip(*pairs, strict=True)
    return random.choices(values, weights=weights, k=1)[0]


def already_seeded(session: Session) -> bool:
    return session.execute(select(User).limit(1)).first() is not None


def seed_users(session: Session) -> list[int]:
    print(f"Seeding {N_USERS} users...", flush=True)
    rows = []
    seen_emails: set[str] = set()
    for _ in range(N_USERS):
        # Faker can produce dup emails; ensure uniqueness.
        for _ in range(5):
            email = fake.unique.email() if fake.unique else fake.email()
            if email not in seen_emails:
                seen_emails.add(email)
                break
        signup = fake.date_time_between(start_date=START, end_date=NOW, tzinfo=timezone.utc)
        rows.append(
            {
                "email": email,
                "full_name": fake.name(),
                "country": fake.country_code(),
                "is_active": random.random() > 0.05,
                "signup_date": signup,
            }
        )
    session.bulk_insert_mappings(User, rows)
    session.flush()
    ids = list(session.execute(select(User.id)).scalars())
    return ids


def seed_accounts(session: Session, user_ids: list[int]) -> list[tuple[int, str]]:
    print(f"Seeding {N_ACCOUNTS} accounts...", flush=True)
    rows = []
    for _ in range(N_ACCOUNTS):
        owner = random.choice(user_ids)
        tier = random.choices(PLAN_TIERS, weights=PLAN_TIER_WEIGHTS, k=1)[0]
        created = fake.date_time_between(start_date=START, end_date=NOW, tzinfo=timezone.utc)
        rows.append(
            {
                "owner_user_id": owner,
                "name": fake.company(),
                "plan_tier": tier,
                "created_at": created,
            }
        )
    session.bulk_insert_mappings(Account, rows)
    session.flush()
    return list(
        session.execute(select(Account.id, Account.plan_tier, Account.created_at)).all()
    )


def seed_subscriptions(session: Session, accounts: list) -> list[tuple]:
    print(f"Seeding ~{N_SUBSCRIPTIONS_TARGET} subscriptions...", flush=True)
    rows = []
    # Only paid tiers get subscriptions.
    paid_accounts = [(aid, tier, created) for (aid, tier, created) in accounts if tier != "free"]

    # Hand out 1-4 subscriptions per paid account until we hit the target.
    while len(rows) < N_SUBSCRIPTIONS_TARGET and paid_accounts:
        for aid, tier, created in paid_accounts:
            if len(rows) >= N_SUBSCRIPTIONS_TARGET:
                break
            n_subs = random.choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05], k=1)[0]
            for _ in range(n_subs):
                interval = random.choices(
                    [BillingInterval.monthly, BillingInterval.yearly],
                    weights=[0.8, 0.2],
                    k=1,
                )[0]
                plan_key = f"{tier}_{interval.value}"
                amount_cents = PLAN_PRICING_CENTS[plan_key]
                status: SubscriptionStatus = weighted_choice(STATUS_WEIGHTS)  # type: ignore[assignment]
                started = fake.date_time_between(
                    start_date=created, end_date=NOW, tzinfo=timezone.utc
                )
                canceled = None
                if status == SubscriptionStatus.cancelled:
                    canceled = fake.date_time_between(
                        start_date=started, end_date=NOW, tzinfo=timezone.utc
                    )
                rows.append(
                    {
                        "account_id": aid,
                        "plan_name": plan_key,
                        "amount_cents": amount_cents,
                        "currency": "USD",
                        "billing_interval": interval,
                        "status": status,
                        "started_at": started,
                        "canceled_at": canceled,
                    }
                )

    session.bulk_insert_mappings(Subscription, rows)
    session.flush()
    return list(
        session.execute(
            select(
                Subscription.id,
                Subscription.account_id,
                Subscription.amount_cents,
                Subscription.billing_interval,
                Subscription.started_at,
            )
        ).all()
    )


def seed_transactions(session: Session, subscriptions: list) -> None:
    print(f"Seeding ~{N_TRANSACTIONS_TARGET} transactions...", flush=True)
    rows: list[dict] = []
    # ~33 transactions per subscription on average → ~50k
    target_per_sub = N_TRANSACTIONS_TARGET // max(len(subscriptions), 1)

    for sub_id, account_id, amount_cents, interval, started in subscriptions:
        n_tx = max(1, int(random.gauss(target_per_sub, target_per_sub * 0.3)))
        for _ in range(n_tx):
            status = random.choices(
                [
                    TransactionStatus.succeeded,
                    TransactionStatus.failed,
                    TransactionStatus.refunded,
                ],
                weights=[0.92, 0.06, 0.02],
                k=1,
            )[0]
            occurred = fake.date_time_between(
                start_date=started, end_date=NOW, tzinfo=timezone.utc
            )
            rows.append(
                {
                    "account_id": account_id,
                    "subscription_id": sub_id,
                    "amount_cents": amount_cents,
                    "currency": "USD",
                    "status": status,
                    "occurred_at": occurred,
                }
            )

        # Flush in chunks to keep memory reasonable.
        if len(rows) >= 10_000:
            session.bulk_insert_mappings(Transaction, rows)
            session.flush()
            rows = []

    if rows:
        session.bulk_insert_mappings(Transaction, rows)
        session.flush()


def seed_events(session: Session, user_ids: list[int], accounts: list) -> None:
    print(f"Seeding ~{N_EVENTS_TARGET} events...", flush=True)
    account_ids = [aid for (aid, _, _) in accounts]
    rows: list[dict] = []
    for _ in range(N_EVENTS_TARGET):
        uid = random.choice(user_ids) if random.random() > 0.05 else None
        aid = random.choice(account_ids) if random.random() > 0.15 else None
        name = random.choice(EVENT_NAMES)
        occurred = fake.date_time_between(start_date=START, end_date=NOW, tzinfo=timezone.utc)
        rows.append(
            {
                "user_id": uid,
                "account_id": aid,
                "event_name": name,
                "occurred_at": occurred,
                "properties": None,
            }
        )
        if len(rows) >= 20_000:
            session.bulk_insert_mappings(Event, rows)
            session.flush()
            rows = []
    if rows:
        session.bulk_insert_mappings(Event, rows)
        session.flush()


def main() -> int:
    with engine.connect() as conn:
        conn.execute(__import__("sqlalchemy").text("SELECT 1"))

    with SessionLocal() as session:
        if already_seeded(session):
            print("Tables already non-empty; skipping. Drop & re-migrate to re-seed.")
            return 0

        user_ids = seed_users(session)
        accounts = seed_accounts(session, user_ids)
        subs = seed_subscriptions(session, accounts)
        seed_transactions(session, subs)
        seed_events(session, user_ids, accounts)

        session.commit()
        print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
