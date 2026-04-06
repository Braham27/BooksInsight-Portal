const VALID_FILING_STATUSES = new Set(["SINGLE", "MFJ", "MFS", "HOH", "QSS"]);

interface ValidationIssue {
  field: string;
  message: string;
  severity: "error" | "warning";
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
}

export function validateTaxFacts(factsData: Record<string, unknown>): ValidationResult {
  const errors: ValidationIssue[] = [];
  const warnings: ValidationIssue[] = [];

  // Filing status
  const filingStatus = factsData.filing_status as string | undefined;
  if (!filingStatus) {
    errors.push({ field: "filing_status", message: "Filing status is required", severity: "error" });
  } else if (!VALID_FILING_STATUSES.has(filingStatus)) {
    errors.push({
      field: "filing_status",
      message: `Invalid filing status: ${filingStatus}. Must be one of: ${[...VALID_FILING_STATUSES].sort().join(", ")}`,
      severity: "error",
    });
  }

  // Tax year
  if (!factsData.tax_year) {
    errors.push({ field: "tax_year", message: "Tax year is required", severity: "error" });
  }

  // Income validation
  const income = factsData.income as { w2?: Array<Record<string, unknown>> } | undefined;
  const w2List = income?.w2 ?? [];

  if (w2List.length === 0) {
    warnings.push({
      field: "income.w2",
      message: "No W-2 income data found. If you have W-2 income, please upload your W-2 or enter the amounts.",
      severity: "warning",
    });
  }

  for (let i = 0; i < w2List.length; i++) {
    const w2 = w2List[i];
    const prefix = `income.w2[${i}]`;
    const wages = (w2.wages_box1 as number) ?? 0;
    const withheld = (w2.fed_withheld_box2 as number) ?? 0;

    if (wages < 0) {
      errors.push({ field: `${prefix}.wages_box1`, message: "Wages cannot be negative", severity: "error" });
    }
    if (withheld < 0) {
      errors.push({ field: `${prefix}.fed_withheld_box2`, message: "Federal withholding cannot be negative", severity: "error" });
    }
    if (withheld > wages && wages > 0) {
      errors.push({
        field: `${prefix}.fed_withheld_box2`,
        message: `Federal withholding ($${withheld.toLocaleString()}) exceeds wages ($${wages.toLocaleString()})`,
        severity: "error",
      });
    } else if (wages > 0 && withheld > wages * 0.5) {
      warnings.push({
        field: `${prefix}.fed_withheld_box2`,
        message: "Federal withholding is more than 50% of wages. Please verify this is correct.",
        severity: "warning",
      });
    }

    const ssWages = (w2.ss_wages_box3 as number) ?? 0;
    if (ssWages < 0) {
      errors.push({ field: `${prefix}.ss_wages_box3`, message: "Social security wages cannot be negative", severity: "error" });
    }
  }

  // Payment validation
  const payments = factsData.payments as { fed_income_tax_withheld?: number } | undefined;
  const totalWithheld = payments?.fed_income_tax_withheld ?? 0;
  if (totalWithheld < 0) {
    errors.push({
      field: "payments.fed_income_tax_withheld",
      message: "Total federal income tax withheld cannot be negative",
      severity: "error",
    });
  }

  // Dependent validation
  const dependents = (factsData.dependents as Array<Record<string, unknown>>) ?? [];
  for (let i = 0; i < dependents.length; i++) {
    const dep = dependents[i];
    if (!dep.first_name) {
      warnings.push({ field: `dependents[${i}].first_name`, message: "Dependent first name is missing", severity: "warning" });
    }
    if (!dep.last_name) {
      warnings.push({ field: `dependents[${i}].last_name`, message: "Dependent last name is missing", severity: "warning" });
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}
