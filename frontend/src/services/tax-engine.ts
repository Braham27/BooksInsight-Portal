/**
 * Tax engine adapter — TypeScript implementation of federal tax computation.
 *
 * For MVP: uses 2025 federal tax brackets (standard deduction, W-2 only).
 * For production: delegates to Tax-Calculator via Python serverless function.
 */

interface TaxFactsData {
  tax_year?: number;
  filing_status?: string;
  primary_taxpayer?: {
    is_over_65?: boolean;
    is_blind?: boolean;
  };
  spouse?: {
    is_over_65?: boolean;
    is_blind?: boolean;
  };
  income?: {
    w2?: Array<{
      wages_box1?: number;
      fed_withheld_box2?: number;
      employer_name?: string;
    }>;
  };
  dependents?: Array<Record<string, unknown>>;
  payments?: {
    fed_income_tax_withheld?: number;
  };
}

interface TaxLineItem {
  label: string;
  value: number;
  line_ref: string | null;
}

export interface ComputeResult {
  tax_year: number;
  total_income: number;
  adjusted_gross_income: number;
  standard_deduction: number;
  taxable_income: number;
  income_tax: number;
  payroll_tax: number;
  total_tax: number;
  withholding: number;
  refund_or_balance: number;
  line_items: TaxLineItem[];
  engine_name: string;
  engine_version: string;
  _fallback?: boolean;
  _warning?: string;
}

// 2025 standard deductions
const STD_DEDUCTIONS: Record<string, number> = {
  SINGLE: 15000,
  MFJ: 30000,
  MFS: 15000,
  HOH: 22500,
  QSS: 30000,
};

type Bracket = [number, number];

// 2025 federal tax brackets
const BRACKETS: Record<string, Bracket[]> = {
  SINGLE: [
    [11925, 0.10],
    [48475, 0.12],
    [103350, 0.22],
    [197300, 0.24],
    [250525, 0.32],
    [626350, 0.35],
    [Infinity, 0.37],
  ],
  MFJ: [
    [23850, 0.10],
    [96950, 0.12],
    [206700, 0.22],
    [394600, 0.24],
    [501050, 0.32],
    [751600, 0.35],
    [Infinity, 0.37],
  ],
  QSS: [
    [23850, 0.10],
    [96950, 0.12],
    [206700, 0.22],
    [394600, 0.24],
    [501050, 0.32],
    [751600, 0.35],
    [Infinity, 0.37],
  ],
  MFS: [
    [11925, 0.10],
    [48475, 0.12],
    [103350, 0.22],
    [197300, 0.24],
    [250525, 0.32],
    [626350, 0.35],
    [Infinity, 0.37],
  ],
  HOH: [
    [17000, 0.10],
    [64850, 0.12],
    [103350, 0.22],
    [197300, 0.24],
    [250500, 0.32],
    [626350, 0.35],
    [Infinity, 0.37],
  ],
};

function computeBracketTax(taxableIncome: number, brackets: Bracket[]): number {
  let tax = 0;
  let prevLimit = 0;
  let remaining = taxableIncome;

  for (const [limit, rate] of brackets) {
    const bracketIncome = Math.min(remaining, limit - prevLimit);
    if (bracketIncome <= 0) break;
    tax += bracketIncome * rate;
    remaining -= bracketIncome;
    prevLimit = limit;
  }

  return tax;
}

export function computeTaxes(factsData: TaxFactsData, taxYear: number): ComputeResult {
  const filingStatus = factsData.filing_status ?? "SINGLE";
  const w2List = factsData.income?.w2 ?? [];
  const totalWages = w2List.reduce((sum, w) => sum + (w.wages_box1 ?? 0), 0);
  const totalWithheld = factsData.payments?.fed_income_tax_withheld ?? 0;

  // Standard deduction
  let standardDeduction = STD_DEDUCTIONS[filingStatus] ?? 15000;

  // Age/blind adjustments
  const primary = factsData.primary_taxpayer;
  const isMarried = filingStatus === "MFJ" || filingStatus === "MFS" || filingStatus === "QSS";
  const ageBlindAdd = isMarried ? 1300 : 1600;

  if (primary?.is_over_65) standardDeduction += ageBlindAdd;
  if (primary?.is_blind) standardDeduction += ageBlindAdd;

  const spouse = factsData.spouse;
  if (spouse?.is_over_65) standardDeduction += 1300;
  if (spouse?.is_blind) standardDeduction += 1300;

  // Compute
  const taxableIncome = Math.max(0, totalWages - standardDeduction);
  const brackets = BRACKETS[filingStatus] ?? BRACKETS.SINGLE;
  const incomeTax = Math.round(computeBracketTax(taxableIncome, brackets) * 100) / 100;
  const refundOrBalance = Math.round((totalWithheld - incomeTax) * 100) / 100;

  return {
    tax_year: taxYear,
    total_income: totalWages,
    adjusted_gross_income: totalWages,
    standard_deduction: standardDeduction,
    taxable_income: taxableIncome,
    income_tax: incomeTax,
    payroll_tax: 0,
    total_tax: incomeTax,
    withholding: totalWithheld,
    refund_or_balance: refundOrBalance,
    line_items: [
      { label: "Total W-2 Wages", value: totalWages, line_ref: "Line 1a" },
      { label: "Adjusted Gross Income", value: totalWages, line_ref: "Line 11" },
      { label: "Standard Deduction", value: standardDeduction, line_ref: "Line 13" },
      { label: "Taxable Income", value: taxableIncome, line_ref: "Line 15" },
      { label: "Income Tax", value: incomeTax, line_ref: "Line 16" },
      { label: "Federal Tax Withheld", value: totalWithheld, line_ref: "Line 25a" },
      {
        label: refundOrBalance >= 0 ? "Refund" : "Amount Owed",
        value: Math.abs(refundOrBalance),
        line_ref: refundOrBalance >= 0 ? "Line 34" : "Line 37",
      },
    ],
    engine_name: "booksinsight-tax-engine",
    engine_version: "1.0.0-mvp",
    _fallback: true,
    _warning:
      "Computed using simplified 2025 federal tax brackets. Results are estimates.",
  };
}
