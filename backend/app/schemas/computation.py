from datetime import datetime

from pydantic import BaseModel


class TaxLineItem(BaseModel):
    label: str
    value: float
    line_ref: str | None = None


class ComputationResult(BaseModel):
    tax_year: int
    total_income: float
    adjusted_gross_income: float
    standard_deduction: float
    taxable_income: float
    income_tax: float
    payroll_tax: float
    total_tax: float
    withholding: float
    refund_or_balance: float
    line_items: list[TaxLineItem] = []


class ComputationResponse(BaseModel):
    id: str
    case_id: str
    tax_year: int
    results: ComputationResult
    explanation: str | None = None
    engine_meta: dict
    created_at: datetime

    model_config = {"from_attributes": True}
