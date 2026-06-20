import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum as SAEnum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SubscriptionStatus(str, enum.Enum):
    # NOTE: deliberately missing `paused`. Scenario 3 adds it via ALTER TYPE.
    # fct_mrr filters `status IN ('active', 'trialing')`, so a new value
    # silently drops out of MRR until the filter is updated.
    active = "active"
    trialing = "trialing"
    cancelled = "cancelled"


class BillingInterval(str, enum.Enum):
    monthly = "monthly"
    yearly = "yearly"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # NOTE: deliberately named `amount_cents`, type BigInteger.
    # Scenario 2's PR renames this to `amount`, switches to NUMERIC(12,2),
    # and backfills `amount = amount_cents / 100`. Every model still compiles,
    # but stg_subscriptions still divides by 100, so fct_mrr ends up 100x low.
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)

    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    billing_interval: Mapped[BillingInterval] = mapped_column(
        SAEnum(BillingInterval, name="billing_interval", create_type=False),
        nullable=False,
        default=BillingInterval.monthly,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus, name="subscription_status", create_type=False),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    account: Mapped["Account"] = relationship(back_populates="subscriptions")  # noqa: F821
    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        back_populates="subscription"
    )
