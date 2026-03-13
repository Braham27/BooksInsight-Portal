from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clerk import AuthUser, get_current_user
from app.database import get_db
from app.models.case import Case, CaseStatus
from app.models.computation import Computation
from app.models.tax_facts import TaxFact
from app.schemas.computation import ComputationResponse
from app.services import audit_service
from app.services.engine_adapter import tax_calc_adapter
from app.services.explanation_service import generate_explanation

router = APIRouter(prefix="/cases/{case_id}", tags=["computation"])


@router.post("/compute", response_model=ComputationResponse)
async def compute_taxes(
    case_id: str,
    request: Request,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(TaxFact)
        .where(TaxFact.case_id == case_id)
        .order_by(TaxFact.version.desc())
    )
    facts = result.scalars().first()
    if not facts:
        raise HTTPException(status_code=400, detail="No tax facts available. Complete intake first.")

    case.status = CaseStatus.COMPUTING
    await db.flush()

    comp_result = tax_calc_adapter.compute(facts.facts_data, case.tax_year)

    explanation = await generate_explanation(comp_result, facts.facts_data)

    computation = Computation(
        case_id=case_id,
        engine_name=comp_result.get("engine_name", "tax-calculator"),
        engine_version=comp_result.get("engine_version", "unknown"),
        input_payload=facts.facts_data,
        output_payload=comp_result,
        explanation=explanation,
    )
    db.add(computation)
    await db.flush()

    case.status = CaseStatus.REVIEW
    await db.flush()

    await audit_service.log_event(
        db,
        user_id=user.user_id,
        action="computation_completed",
        entity_type="computation",
        entity_id=computation.id,
        case_id=case_id,
        new_value={"engine": computation.engine_name, "refund_or_balance": comp_result.get("refund_or_balance")},
        ip_address=request.client.host if request.client else None,
    )

    return ComputationResponse(
        id=computation.id,
        case_id=case_id,
        engine_name=computation.engine_name,
        engine_version=computation.engine_version,
        result=comp_result,
        explanation=explanation,
        created_at=computation.created_at,
    )


@router.get("/computation", response_model=ComputationResponse)
async def get_latest_computation(
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
        select(Computation)
        .where(Computation.case_id == case_id)
        .order_by(Computation.created_at.desc())
    )
    comp = result.scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="No computation found")

    return ComputationResponse(
        id=comp.id,
        case_id=case_id,
        engine_name=comp.engine_name,
        engine_version=comp.engine_version,
        result=comp.output_payload,
        explanation=comp.explanation,
        created_at=comp.created_at,
    )
