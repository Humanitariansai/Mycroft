from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    plan_tier: Mapped[str] = mapped_column(String(20), nullable=False, default="free", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="accounts")  # noqa: F821
    subscriptions: Mapped[list["Subscription"]] = relationship(  # noqa: F821
        back_populates="account"
    )
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")  # noqa: F821
    events: Mapped[list["Event"]] = relationship(back_populates="account")  # noqa: F821
