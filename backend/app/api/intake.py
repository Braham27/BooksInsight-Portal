from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clerk import AuthUser, get_current_user
from app.database import get_db
from app.models.case import Case, CaseStatus
from app.schemas.tax_facts import NormalizeResponse
from app.services.interview_service import normalize_facts

router = APIRouter(prefix="/cases/{case_id}", tags=["intake"])


@router.post("/normalize", response_model=NormalizeResponse)
async def normalize_tax_facts(
    case_id: str,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await normalize_facts(db, case, user.user_id)

    case.status = CaseStatus.VALIDATING
    await db.flush()

    return result
