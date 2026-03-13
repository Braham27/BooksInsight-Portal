from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clerk import AuthUser, get_current_user
from app.database import get_db
from app.models.case import Case
from app.models.tax_facts import TaxFact
from app.schemas.validation import ValidationResponse
from app.services.validation_service import validate_tax_facts

router = APIRouter(prefix="/cases/{case_id}", tags=["validation"])


@router.post("/validate", response_model=ValidationResponse)
async def validate_case(
    case_id: str,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.user_id != user.user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(TaxFact)
        .where(TaxFact.case_id == case_id)
        .order_by(TaxFact.version.desc())
    )
    facts = result.scalars().first()
    if not facts:
        raise HTTPException(status_code=400, detail="No tax facts to validate. Run normalize first.")

    validation = validate_tax_facts(facts.facts_data, case.tax_year)
    return validation
