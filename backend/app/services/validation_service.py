import structlog

from app.schemas.tax_facts import TaxFactsData
from app.schemas.validation import ValidationError_, ValidationResponse

logger = structlog.get_logger()

VALID_FILING_STATUSES = {"SINGLE", "MFJ", "MFS", "HOH", "QSS"}


def validate_tax_facts(facts_data: dict) -> ValidationResponse:
    """Validate tax facts before computation. Returns errors (blocking) and warnings."""
    errors: list[ValidationError_] = []
    warnings: list[ValidationError_] = []

    # ---- Required fields ----
    if not facts_data.get("filing_status"):
        errors.append(ValidationError_(
            field="filing_status",
            message="Filing status is required",
            severity="error",
        ))
    elif facts_data["filing_status"] not in VALID_FILING_STATUSES:
        errors.append(ValidationError_(
            field="filing_status",
            message=f"Invalid filing status: {facts_data['filing_status']}. Must be one of: {', '.join(sorted(VALID_FILING_STATUSES))}",
            severity="error",
        ))

    if not facts_data.get("tax_year"):
        errors.append(ValidationError_(
            field="tax_year",
            message="Tax year is required",
            severity="error",
        ))

    # ---- Income validation ----
    w2_list = facts_data.get("income", {}).get("w2", [])
    if not w2_list:
        warnings.append(ValidationError_(
            field="income.w2",
            message="No W-2 income data found. If you have W-2 income, please upload your W-2 or enter the amounts.",
            severity="warning",
        ))

    for i, w2 in enumerate(w2_list):
        prefix = f"income.w2[{i}]"
        wages = w2.get("wages_box1", 0)
        withheld = w2.get("fed_withheld_box2", 0)

        # Non-negative checks
        if wages < 0:
            errors.append(ValidationError_(
                field=f"{prefix}.wages_box1",
                message="Wages cannot be negative",
                severity="error",
            ))

        if withheld < 0:
            errors.append(ValidationError_(
                field=f"{prefix}.fed_withheld_box2",
                message="Federal withholding cannot be negative",
                severity="error",
            ))

        # Withholding reasonableness check
        if withheld > wages and wages > 0:
            errors.append(ValidationError_(
                field=f"{prefix}.fed_withheld_box2",
                message=f"Federal withholding (${withheld:,.2f}) exceeds wages (${wages:,.2f})",
                severity="error",
            ))
        elif wages > 0 and withheld > wages * 0.5:
            warnings.append(ValidationError_(
                field=f"{prefix}.fed_withheld_box2",
                message=f"Federal withholding is more than 50% of wages. Please verify this is correct.",
                severity="warning",
            ))

        # SS wages check
        ss_wages = w2.get("ss_wages_box3", 0)
        if ss_wages < 0:
            errors.append(ValidationError_(
                field=f"{prefix}.ss_wages_box3",
                message="Social security wages cannot be negative",
                severity="error",
            ))

    # ---- Payment validation ----
    total_withheld = facts_data.get("payments", {}).get("fed_income_tax_withheld", 0)
    if total_withheld < 0:
        errors.append(ValidationError_(
            field="payments.fed_income_tax_withheld",
            message="Total federal income tax withheld cannot be negative",
            severity="error",
        ))

    # ---- Dependent validation ----
    dependents = facts_data.get("dependents", [])
    for i, dep in enumerate(dependents):
        if not dep.get("first_name"):
            warnings.append(ValidationError_(
                field=f"dependents[{i}].first_name",
                message="Dependent first name is missing",
                severity="warning",
            ))
        if not dep.get("last_name"):
            warnings.append(ValidationError_(
                field=f"dependents[{i}].last_name",
                message="Dependent last name is missing",
                severity="warning",
            ))

    is_valid = len(errors) == 0

    logger.info(
        "validation_complete",
        valid=is_valid,
        error_count=len(errors),
        warning_count=len(warnings),
    )

    return ValidationResponse(valid=is_valid, errors=errors, warnings=warnings)
