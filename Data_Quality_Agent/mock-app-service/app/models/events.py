from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    account_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("accounts.id", ondelete="SET NULL"), index=True
    )
    event_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    properties: Mapped[dict | None] = mapped_column(JSONB)

    user: Mapped["User | None"] = relationship(back_populates="events")  # noqa: F821
    account: Mapped["Account | None"] = relationship(back_populates="events")  # noqa: F821
