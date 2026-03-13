from pydantic import BaseModel, Field


class W2Income(BaseModel):
    employer_name: str | None = None
    employer_ein: str | None = None
    wages_box1: float = 0.0
    fed_withheld_box2: float = 0.0
    ss_wages_box3: float = 0.0
    ss_tax_box4: float = 0.0
    medicare_wages_box5: float = 0.0
    medicare_tax_box6: float = 0.0
    state: str | None = None
    state_wages: float = 0.0
    state_tax_withheld: float = 0.0
    employee_name: str | None = None
    ssn_last4: str | None = None


class Dependent(BaseModel):
    first_name: str
    last_name: str
    ssn_last4: str | None = None
    date_of_birth: str | None = None
    relationship: str | None = None
    months_lived_with: int = Field(default=12, ge=0, le=12)


class PrimaryTaxpayer(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: str | None = None
    ssn_last4: str | None = None
    is_blind: bool = False
    is_over_65: bool = False


class IncomeData(BaseModel):
    w2: list[W2Income] = []


class PaymentData(BaseModel):
    fed_income_tax_withheld: float = 0.0


class TaxFactsData(BaseModel):
    tax_year: int = 2025
    filing_status: str | None = None
    primary_taxpayer: PrimaryTaxpayer | None = None
    spouse: PrimaryTaxpayer | None = None
    income: IncomeData = IncomeData()
    dependents: list[Dependent] = []
    payments: PaymentData = PaymentData()


class NormalizeRequest(BaseModel):
    force: bool = False


class NormalizeResponse(BaseModel):
    tax_facts: TaxFactsData
    unresolved_questions: list[str] = []
    validation_errors: list[str] = []
