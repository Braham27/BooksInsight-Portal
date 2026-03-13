import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin, UUIDMixin


class CaseStatus(str, enum.Enum):
    INTAKE = "intake"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    COMPUTING = "computing"
    REVIEW = "review"
    COMPLETE = "complete"


class FilingStatus(str, enum.Enum):
    SINGLE = "SINGLE"
    MFJ = "MFJ"
    MFS = "MFS"
    HOH = "HOH"
    QSS = "QSS"


class Case(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cases"

    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus), default=CaseStatus.INTAKE, nullable=False
    )
    tax_year: Mapped[int] = mapped_column(nullable=False, default=2025)
    filing_status: Mapped[str | None] = mapped_column(String(10), nullable=True)
    taxpayer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        back_populates="case", cascade="all, delete-orphan"
    )
    tax_facts: Mapped[list["TaxFact"]] = relationship(  # noqa: F821
        back_populates="case", cascade="all, delete-orphan"
    )
    computations: Mapped[list["Computation"]] = relationship(  # noqa: F821
        back_populates="case", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(  # noqa: F821
        back_populates="case", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(  # noqa: F821
        back_populates="case", cascade="all, delete-orphan"
    )
