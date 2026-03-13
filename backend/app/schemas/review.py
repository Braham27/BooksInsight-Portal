from datetime import datetime

from pydantic import BaseModel

from app.models.review import ReviewDecision


class ReviewCreate(BaseModel):
    decision: ReviewDecision
    notes: str | None = None


class ReviewResponse(BaseModel):
    id: str
    case_id: str
    reviewer_id: str
    decision: ReviewDecision
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
