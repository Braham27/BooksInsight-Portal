// ---- Enums ----
export type CaseStatus =
  | "intake"
  | "extracting"
  | "validating"
  | "computing"
  | "review"
  | "complete";

export type FilingStatus = "single" | "mfj" | "mfs" | "hoh" | "qss";

export type DocType = "w2" | "1099_int" | "1099_div" | "1099_b" | "other";

export type DocStatus =
  | "uploaded"
  | "processing"
  | "extracted"
  | "verified"
  | "error";

export type MessageRole = "user" | "assistant" | "system";

export type ReviewDecision = "approved" | "rejected" | "needs_changes";

// ---- Cases ----
export interface CaseResponse {
  id: string;
  user_id: string;
  tax_year: number;
  status: CaseStatus;
  filing_status: FilingStatus | null;
  created_at: string;
  updated_at: string;
}

export interface CaseCreateRequest {
  tax_year?: number;
}

// ---- Documents ----
export interface DocumentResponse {
  id: string;
  case_id: string;
  file_path: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  doc_type: DocType | null;
  status: DocStatus;
  extracted_data: Record<string, unknown> | null;
  evidence: Record<string, unknown> | null;
  confidence: number | null;
  created_at: string;
}

export interface ExtractionResponse {
  document_id: string;
  doc_type: DocType | null;
  extracted_data: Record<string, unknown>;
  confidence: number;
  status: DocStatus;
}

// ---- Chat ----
export interface ChatMessageResponse {
  id: string;
  case_id: string;
  role: MessageRole;
  content: string;
  structured_output: Record<string, unknown> | null;
  created_at: string;
}

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  reply: string;
  progress: InterviewProgress;
  structured_output: Record<string, unknown> | null;
}

export interface InterviewProgress {
  current_step: string;
  steps_completed: string[];
  steps_remaining: string[];
  percent_complete: number;
}

// ---- Tax Facts ----
export interface TaxFactsData {
  taxpayer: {
    first_name: string;
    last_name: string;
    ssn_last4: string;
    date_of_birth?: string;
  };
  filing_status: FilingStatus;
  income: {
    w2_wages: number;
    w2_withholding: number;
    employers: Array<{
      name: string;
      ein: string;
      wages: number;
      federal_withheld: number;
    }>;
  };
  dependents: Array<{
    first_name: string;
    last_name: string;
    ssn_last4: string;
    relationship: string;
    date_of_birth: string;
  }>;
  payments: {
    federal_withheld: number;
    estimated_payments: number;
  };
}

// ---- Computation ----
export interface TaxLineItem {
  label: string;
  amount: number;
  form_line?: string;
}

export interface ComputationResult {
  line_items: TaxLineItem[];
  total_income: number;
  agi: number;
  standard_deduction: number;
  taxable_income: number;
  income_tax: number;
  payroll_tax: number;
  total_tax: number;
  total_withheld: number;
  refund_or_balance: number;
  engine_name: string;
  engine_version: string;
}

export interface ComputationResponse {
  id: string;
  case_id: string;
  engine_name: string;
  engine_version: string;
  result: ComputationResult;
  explanation: string | null;
  created_at: string;
}

// ---- Validation ----
export interface ValidationError {
  field: string;
  message: string;
  severity: "error" | "warning";
}

export interface ValidationResponse {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
}

// ---- Review ----
export interface ReviewResponse {
  id: string;
  case_id: string;
  reviewer_id: string;
  decision: ReviewDecision;
  notes: string | null;
  created_at: string;
}

export interface ReviewCreateRequest {
  decision: ReviewDecision;
  notes?: string;
}

// ---- Summary ----
export interface CaseSummary {
  case: {
    id: string;
    tax_year: number;
    status: CaseStatus;
    filing_status: FilingStatus | null;
    created_at: string | null;
  };
  documents: Array<{
    id: string;
    file_name: string;
    doc_type: DocType | null;
    status: DocStatus;
  }>;
  tax_facts: TaxFactsData | null;
  computation: {
    engine: string;
    result: ComputationResult;
    explanation: string | null;
  } | null;
  reviews: Array<{
    id: string;
    decision: ReviewDecision;
    notes: string | null;
    created_at: string | null;
  }>;
}
