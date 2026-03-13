from datetime import datetime

from pydantic import BaseModel

from app.models.document import DocStatus


class DocumentResponse(BaseModel):
    id: str
    case_id: str
    doc_type: str
    file_name: str
    file_size: int
    mime_type: str
    status: DocStatus
    extracted_data: dict | None = None
    evidence: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUpdateRequest(BaseModel):
    extracted_data: dict | None = None
    doc_type: str | None = None


class ExtractionResponse(BaseModel):
    document_id: str
    doc_type: str
    extracted_data: dict
    evidence: dict
    warnings: list[str] = []
