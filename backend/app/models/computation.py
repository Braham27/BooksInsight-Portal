from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin, UUIDMixin


class Computation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "computations"

    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    engine_name: Mapped[str] = mapped_column(String(50), nullable=False, default="taxcalc")
    engine_version: Mapped[str] = mapped_column(String(50), nullable=True)
    input_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    explanation: Mapped[str | None] = mapped_column(nullable=True)

    # Relationships
    case: Mapped["Case"] = relationship(back_populates="computations")  # noqa: F821
