# System Architecture

This should be built as a **controlled tax workflow system**, not just a chatbot.

Core rule:

* **AI talks**
* **Rules engine calculates**
* **Humans approve when needed**

That separation is what keeps the product usable and defensible. Tax-Calculator is a good fit for your first version because it is built for US federal income and payroll tax modeling and is permissively licensed for future commercialization.

---

# 1. High-level architecture

```text
User
  ↓
Web app / chat UI
  ↓
Orchestrator API
  ↓
Document pipeline → Structured tax facts → Validation layer
                                      ↓
                              Tax engine adapter
                                      ↓
                              Tax calculation engine
                                      ↓
                           Results + explanations + audit trail
```

---

# 2. Frontend layer

This is what the user sees.

## Main screens

* Chat interface
* Document upload area
* Review / correction screen
* Tax summary screen
* Admin / reviewer screen

## What it does

* accepts PDFs, images, and typed answers
* shows extracted values for confirmation
* lets the user fix mistakes
* displays refund / balance due summary
* lets internal staff review cases

## UX principle

Do **not** make users think in tax form language first.

Good:

* “Upload your W-2”
* “Do you have children you support?”

Bad:

* “Enter line 1a wages”
* “Provide dependent qualification flags”

The app should translate user language into tax structure behind the scenes.

---

# 3. Orchestrator API

This is the brain of the workflow.

## Responsibilities

* manage case/session state
* route uploads to OCR and extraction
* call the LLM for interview questions
* call validation rules
* call the tax engine
* save outputs and audit logs

## Why it matters

Without this layer, you end up with a messy chatbot glued directly to tax logic. That becomes impossible to debug.

---

# 4. Document pipeline

This is where uploaded papers become usable data.

## Flow

1. user uploads file
2. system classifies document type
3. OCR extracts text and layout
4. extraction model maps fields into schema
5. evidence is stored for each extracted field

## Output example

```json
{
  "doc_type": "W2",
  "fields": {
    "employer_name": "Amazon",
    "wages_box1": 72400,
    "fed_withheld_box2": 9200
  },
  "evidence": {
    "wages_box1": { "page": 1, "bbox": [100, 210, 220, 240], "confidence": 0.98 },
    "fed_withheld_box2": { "page": 1, "bbox": [300, 210, 380, 240], "confidence": 0.97 }
  }
}
```

## Critical design rule

Every extracted value should have:

* source document
* page
* location
* confidence score

If you skip that, your internal team will not trust the system.

---

# 5. Canonical tax facts layer

This is the most important data model in the whole app.

You need one clean internal schema that represents the case before it is transformed into engine-specific inputs.

## Example

```json
{
  "tax_year": 2025,
  "filing_status": "SINGLE",
  "primary_taxpayer": {
    "first_name": "John",
    "last_name": "Doe",
    "dob": "1990-04-10"
  },
  "income": {
    "w2": [
      {
        "employer_name": "Amazon",
        "wages_box1": 72400,
        "fed_withheld_box2": 9200
      }
    ]
  },
  "dependents": [],
  "payments": {
    "fed_income_tax_withheld": 9200
  }
}
```

## Why this matters

You do **not** want your app tightly coupled to one engine’s variable names.

Your internal schema should stay stable even if:

* you upgrade the tax engine
* you add state taxes later
* you swap engines later

---

# 6. Validation layer

This is the gatekeeper between AI and tax math.

## It should check

* required fields exist
* filing status is valid
* numbers are non-negative where appropriate
* totals reconcile
* document data and user answers do not conflict
* confidence thresholds are met

## Example

If the AI extracts W-2 wages of $72,400 but the user typed $7,240:

* do not silently choose one
* flag conflict
* ask for confirmation

## Rule

**No calculation should run on unresolved critical conflicts.**

---

# 7. LLM layer

The LLM should do only three things.

## Allowed responsibilities

* ask questions
* summarize/explain results
* convert messy language or OCR output into structured draft data

## Not allowed

* final tax math
* invent missing numbers
* override validation rules
* decide uncertain legal eligibility without escalation

## Example

Allowed:

> “I found one W-2 and federal withholding of $9,200. Do you have any 1099 forms?”

Not allowed:

> “You probably qualify for this credit, so I applied it.”

That second behavior will burn you.

---

# 8. Tax engine adapter

This is the translation layer between your clean schema and Tax-Calculator inputs.

Tax-Calculator expects specific input variables such as filing status codes, wages, and dependent counters, and accepts records through structured data inputs like DataFrames/CSV.

## Example mapping

Your schema:

```json
{
  "filing_status": "MFJ",
  "income": { "w2_total": 75000 },
  "dependents_under_17": 1
}
```

Engine payload:

```json
{
  "RECID": 1,
  "MARS": 2,
  "e00200": 75000,
  "n24": 1
}
```

## Why adapter matters

If you hardcode engine variables throughout your app, your whole system becomes fragile.

---

# 9. Tax calculation engine

For your first version, this should be a dedicated service wrapping **Tax-Calculator**.

## Responsibilities

* receive validated inputs
* run deterministic tax calculations
* return results and line items
* return engine version and tax year used

## Output example

```json
{
  "tax_year": 2025,
  "results": {
    "total_income": 75000,
    "taxable_income": 60400,
    "income_tax": 7830,
    "withholding": 9200,
    "refund": 1370
  },
  "engine_meta": {
    "engine": "taxcalc",
    "version": "x.y.z"
  }
}
```

---

# 10. Explanation layer

This is where the app becomes valuable to humans.

## What it does

Turns engine outputs into plain language.

Example:

* “Your refund is positive because withholding exceeded final tax liability.”
* “Your taxable income is lower than wages because the standard deduction reduced it.”

## Important

The explanation layer should only explain **already computed values**.

It should never compute new results itself.

---

# 11. Audit trail

This is mandatory.

IRS security guidance for tax professionals emphasizes audit logs and tracking activity and changes.

## Track everything

* who uploaded which file
* what the extractor read
* what the user changed
* what the reviewer approved
* which engine version ran
* what results were shown

## Why this matters

When a number looks wrong, you need to answer:

* where did it come from?
* who changed it?
* when?
* based on which document?
* under which tax-year rules?

Without that, you cannot scale internal trust.

---

# 12. Human review layer

Even for internal use, you need review gates.

## Recommended checkpoints

* low-confidence extraction review
* filing status review
* dependent review
* final tax summary review

## Later

When you get PTIN/EFIN and decide to operationalize filing, this review layer becomes your compliance control point. PTIN is required for compensated preparation, and e-filing for clients generally requires authorized e-file provider status.

---

# 13. Data storage design

Use separate stores.

## Recommended split

* **Object storage** for raw uploaded files
* **Relational DB** for structured tax facts and case state
* **Audit log store** for immutable event history

## Why split them

Raw files and structured tax data have different access patterns and security needs.

---

# 14. Security architecture

Taxpayer data is sensitive PII. IRS guidance for tax professionals and NIST guidance both support strong protections like access control, encryption, and auditability.

## Minimum controls

* encryption at rest
* encryption in transit
* role-based access
* MFA for staff
* least privilege
* separate prod/dev environments
* secrets in a KMS or vault
* SSN masking in UI and logs

## Hard truth

If you build the AI before the security controls, you are building backwards.

---

# 15. Suggested internal API endpoints

## Core endpoints

* `POST /cases`
* `POST /cases/{id}/documents`
* `POST /cases/{id}/extract`
* `POST /cases/{id}/normalize`
* `POST /cases/{id}/validate`
* `POST /cases/{id}/compute`
* `POST /cases/{id}/review`
* `GET /cases/{id}/summary`

## Why

This keeps every stage explicit and testable.

---

# 16. Recommended stack

## Frontend

* Next.js
* Tailwind
* component library for admin/review UI

## Backend

* Python FastAPI
* PostgreSQL
* Redis for job queues/session caching

## AI / document layer

* OCR service
* LLM service for interview + extraction assistance
* structured output enforcement

## Tax engine

* Tax-Calculator in isolated Python service

## File storage

* S3-compatible object storage

## Auth

* Clerk, Auth0, or internal SSO if this stays staff-only

---

# 17. Best MVP architecture for you

Given your current position, I would build **only this** first:

## Scope

* US federal only
* W-2 only
* standard deduction only
* no public users
* internal reviewer UI
* no e-file

## Why

Because this is enough to prove:

* upload works
* extraction works
* interview works
* tax engine integration works
* review workflow works

Anything broader right now is distraction.

---

# 18. The biggest product mistake to avoid

Do **not** build this as:

* one chatbot
* one prompt
* one database table
* one “calculate taxes” button

That is a demo, not a system.

Build it as **a pipeline with checkpoints**.

That is what turns it into an internal product you can trust.

---

# Recommended build sequence

## Phase 1

* case/session model
* upload flow
* W-2 extraction
* canonical schema
* validation layer

## Phase 2

* Tax-Calculator adapter
* results page
* explanation layer
* audit log

## Phase 3

* internal reviewer workflow
* confidence thresholds
* correction UI
* reporting dashboard

## Phase 4

* add 1099-INT / DIV
* add more validations
* begin preparer workflow planning

---

If you want, I’ll turn this into a **1-page technical blueprint** with:

* exact modules
* DB tables
* API routes
* MVP sprint plan for first 30 days
