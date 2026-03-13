from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clerk import AuthUser, get_current_user
from app.database import get_db
from app.models.case import Case
from app.models.document import Document, DocStatus
from app.schemas.document import ExtractionResponse
from app.services.document_service import extract_document

router = APIRouter(prefix="/cases/{case_id}", tags=["extraction"])


@router.post("/extract", response_model=list[ExtractionResponse])
async def trigger_extraction(
    case_id: str,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.user_id != user.user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    from sqlalchemy import select

    result = await db.execute(
        select(Document).where(
            Document.case_id == case_id,
            Document.status == DocStatus.UPLOADED,
        )
    )
    docs = result.scalars().all()
    if not docs:
        raise HTTPException(status_code=400, detail="No documents awaiting extraction")

    results = []
    for doc in docs:
        extraction = await extract_document(db, doc, user.user_id)
        results.append(extraction)

    return results
