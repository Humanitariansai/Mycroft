from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(200))
    country: Mapped[str | None] = mapped_column(String(2), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # NOTE: deliberately named `signup_date` (not `created_at`).
    # Scenario 1's PR renames this to `created_at`; stg_users in mock-analytics
    # references this column by name, so the rename breaks dbt compile.
    signup_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    accounts: Mapped[list["Account"]] = relationship(back_populates="owner")  # noqa: F821
    events: Mapped[list["Event"]] = relationship(back_populates="user")  # noqa: F821
