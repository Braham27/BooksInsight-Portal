from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clerk import AuthUser, get_current_user
from app.database import get_db
from app.models.case import Case, CaseStatus
from app.models.computation import Computation
from app.models.document import Document
from app.models.review import Review
from app.models.tax_facts import TaxFact
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services import audit_service

router = APIRouter(prefix="/cases/{case_id}", tags=["review"])


@router.post("/review", response_model=ReviewResponse, status_code=201)
async def submit_review(
    case_id: str,
    body: ReviewCreate,
    request: Request,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.user_id != user.user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    if case.status != CaseStatus.REVIEW:
        raise HTTPException(status_code=400, detail="Case is not in review status")

    review = Review(
        case_id=case_id,
        reviewer_id=user.user_id,
        decision=body.decision,
        notes=body.notes,
    )
    db.add(review)

    if body.decision.value == "approved":
        case.status = CaseStatus.COMPLETE

    await db.flush()

    await audit_service.log_event(
        db,
        user_id=user.user_id,
        action="review_submitted",
        entity_type="review",
        entity_id=review.id,
        case_id=case_id,
        new_value={"decision": body.decision.value, "notes": body.notes},
        ip_address=request.client.host if request.client else None,
    )

    return review


@router.get("/summary")
async def get_case_summary(
    case_id: str,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.user_id != user.user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Documents
    doc_result = await db.execute(
        select(Document).where(Document.case_id == case_id)
    )
    docs = doc_result.scalars().all()

    # Tax facts
    facts_result = await db.execute(
        select(TaxFact)
        .where(TaxFact.case_id == case_id)
        .order_by(TaxFact.version.desc())
    )
    facts = facts_result.scalars().first()

    # Latest computation
    comp_result = await db.execute(
        select(Computation)
        .where(Computation.case_id == case_id)
        .order_by(Computation.created_at.desc())
    )
    computation = comp_result.scalars().first()

    # Reviews
    review_result = await db.execute(
        select(Review)
        .where(Review.case_id == case_id)
        .order_by(Review.created_at.desc())
    )
    reviews = review_result.scalars().all()

    return {
        "case": {
            "id": str(case.id),
            "tax_year": case.tax_year,
            "status": case.status.value,
            "filing_status": case.filing_status.value if case.filing_status else None,
            "created_at": case.created_at.isoformat() if case.created_at else None,
        },
        "documents": [
            {
                "id": str(d.id),
                "file_name": d.file_name,
                "doc_type": d.doc_type.value if d.doc_type else None,
                "status": d.status.value,
            }
            for d in docs
        ],
        "tax_facts": facts.facts_data if facts else None,
        "computation": {
            "engine": computation.engine_name,
            "result": computation.output_payload,
            "explanation": computation.explanation,
        }
        if computation
        else None,
        "reviews": [
            {
                "id": str(r.id),
                "decision": r.decision.value,
                "notes": r.notes,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reviews
        ],
    }
