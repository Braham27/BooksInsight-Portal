from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin, UUIDMixin


class TaxFact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tax_facts"

    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    facts_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    source_map: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    case: Mapped["Case"] = relationship(back_populates="tax_facts")  # noqa: F821
