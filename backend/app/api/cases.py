from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clerk import AuthUser, get_current_user
from app.database import get_db
from app.models.case import Case, CaseStatus
from app.schemas.case import CaseCreate, CaseListResponse, CaseResponse
from app.services import audit_service

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseResponse, status_code=201)
async def create_case(
    body: CaseCreate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = Case(
        user_id=user.user_id,
        tax_year=body.tax_year,
        status=CaseStatus.INTAKE,
    )
    db.add(case)
    await db.flush()

    await audit_service.log_event(
        db,
        user_id=user.user_id,
        action="case_created",
        entity_type="case",
        entity_id=case.id,
        case_id=case.id,
        new_value={"tax_year": body.tax_year},
    )

    return case


@router.get("", response_model=CaseListResponse)
async def list_cases(
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Case)
        .where(Case.user_id == user.user_id)
        .order_by(Case.created_at.desc())
    )
    cases = result.scalars().all()
    return CaseListResponse(cases=cases, total=len(cases))


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.user_id != user.user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return case
