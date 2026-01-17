from __future__ import annotations

from typing import Optional
from sqlalchemy import String, Date, Boolean, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Holiday(Base):
    __tablename__ = "holidays"

    id: Mapped[int] = mapped_column(primary_key=True)
    country_code: Mapped[str] = mapped_column(String(2), default="KE", index=True)

    # The "actual" holiday date (as declared/baseline)
    date: Mapped["date"] = mapped_column(Date, index=True)

    # The "observed" holiday date after applying Sunday rule
    observed_date: Mapped["date"] = mapped_column(Date, index=True)

    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(20), default="public")  # public | special

    # Source metadata for specials
    source: Mapped[str] = mapped_column(String(40), default="baseline")  # baseline | gazette | ministry | manual
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_date: Mapped[Optional["date"]] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        # Unique on country+date+name+type so reruns don't duplicate
        UniqueConstraint("country_code", "date", "name", "type", name="uq_holiday_natural"),
    )
