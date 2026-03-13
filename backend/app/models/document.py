import enum

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin, UUIDMixin


class DocType(str, enum.Enum):
    W2 = "W2"
    W2_1099_INT = "1099_INT"
    W2_1099_DIV = "1099_DIV"
    W2_1099_B = "1099_B"
    OTHER = "OTHER"


class DocStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    VERIFIED = "verified"
    ERROR = "error"


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doc_type: Mapped[str] = mapped_column(
        String(20), default=DocType.OTHER.value, nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[DocStatus] = mapped_column(
        Enum(DocStatus), default=DocStatus.UPLOADED, nullable=False
    )
    extracted_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    case: Mapped["Case"] = relationship(back_populates="documents")  # noqa: F821
