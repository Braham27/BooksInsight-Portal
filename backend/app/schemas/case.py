from datetime import datetime

from pydantic import BaseModel, Field

from app.models.case import CaseStatus


class CaseCreate(BaseModel):
    tax_year: int = Field(default=2025, ge=2020, le=2030)


class CaseResponse(BaseModel):
    id: str
    user_id: str
    status: CaseStatus
    tax_year: int
    filing_status: str | None = None
    taxpayer_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    cases: list[CaseResponse]
    total: int
