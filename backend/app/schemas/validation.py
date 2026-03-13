from pydantic import BaseModel


class ValidationError_(BaseModel):
    field: str
    message: str
    severity: str  # "error" or "warning"


class ValidationResponse(BaseModel):
    valid: bool
    errors: list[ValidationError_] = []
    warnings: list[ValidationError_] = []
