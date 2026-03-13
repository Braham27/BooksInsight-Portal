# Plan: BooksInsight Portal — AI-Assisted Tax Preparation System (MVP)

Build a US-only, internal AI-assisted tax preparation system. The core principle: **LLMs never compute taxes** — they handle intake, document understanding, and conversation; Tax-Calculator handles all tax math. MVP supports W-2 wages, standard deduction, federal only, no e-file.

**Stack**: Python FastAPI + Next.js (TypeScript) monorepo, PostgreSQL, OpenAI GPT-4/Vision, Clerk auth, deployed to Vercel (frontend) + Railway (backend + DB).

---

## Phase 1: Project Scaffolding & Foundation

**Goal**: Set up the monorepo, both apps running locally, database schema, auth integration, and CI/CD pipeline.

### Steps

1. **Initialize monorepo structure**
   Create the following project structure:
   ```
   /
   ├── frontend/              # Next.js 14+ App Router, TypeScript, Tailwind
   ├── backend/               # FastAPI, Python 3.11+
   ├── docs/                  # Existing architecture docs (idea.md, etc.)
   ├── docker-compose.yml     # Local dev: Postgres, Redis, backend, frontend
   ├── .github/
   │   ├── workflows/         # CI: lint, test, deploy
   │   └── instructions/      # Existing codacy config
   ├── README.md
   └── .gitignore
   ```

2. **Scaffold backend (FastAPI)** — *parallel with step 3*
   - Init with Poetry (`pyproject.toml`)
   - Dependencies: `fastapi`, `uvicorn`, `sqlalchemy[asyncio]`, `alembic`, `asyncpg`, `pydantic>=2`, `openai`, `python-multipart`, `taxcalc` (PSLmodels Tax-Calculator), `clerk-backend-api`, `python-jose`, `httpx`
   - Create folder structure:
     ```
     backend/
     ├── app/
     │   ├── main.py                   # FastAPI app factory, CORS, lifespan
     │   ├── config.py                 # Pydantic Settings (env vars)
     │   ├── database.py               # Async SQLAlchemy engine + session
     │   ├── models/                   # SQLAlchemy ORM models
     │   │   ├── case.py               # Case/session model
     │   │   ├── document.py           # Uploaded document metadata
     │   │   ├── tax_facts.py          # Canonical tax facts
     │   │   ├── computation.py        # Engine computation results
     │   │   └── audit_log.py          # Immutable audit events
     │   ├── schemas/                  # Pydantic request/response schemas
     │   │   ├── case.py
     │   │   ├── document.py
     │   │   ├── tax_facts.py
     │   │   ├── computation.py
     │   │   └── intake.py
     │   ├── api/                      # Route handlers
     │   │   ├── cases.py              # POST /cases, GET /cases/{id}
     │   │   ├── documents.py          # POST /cases/{id}/documents
     │   │   ├── extraction.py         # POST /cases/{id}/extract
     │   │   ├── intake.py             # POST /cases/{id}/normalize
     │   │   ├── validation.py         # POST /cases/{id}/validate
     │   │   ├── computation.py        # POST /cases/{id}/compute
     │   │   ├── review.py             # POST /cases/{id}/review
     │   │   ├── chat.py               # POST /cases/{id}/chat (interview)
     │   │   └── summary.py            # GET /cases/{id}/summary
     │   ├── services/                 # Business logic
     │   │   ├── document_service.py   # Doc classification + GPT-4V extraction
     │   │   ├── interview_service.py  # LLM-driven interview orchestrator
     │   │   ├── validation_service.py # Cross-field validation rules
     │   │   ├── engine_adapter.py     # Tax-Calculator adapter (EngineAdapter)
     │   │   ├── explanation_service.py # Turn results into plain language
     │   │   └── audit_service.py      # Audit trail logger
     │   ├── auth/                     # Clerk JWT verification middleware
     │   │   └── clerk.py
     │   └── utils/
     │       └── storage.py            # File storage abstraction (local → S3)
     ├── alembic/                      # DB migrations
     ├── alembic.ini
     ├── tests/
     ├── Dockerfile
     └── pyproject.toml
     ```

3. **Scaffold frontend (Next.js)** — *parallel with step 2*
   - `npx create-next-app@latest frontend --typescript --tailwind --app --src-dir`
   - Dependencies: `@clerk/nextjs`, `@tanstack/react-query`, `axios`, `zustand`, `react-dropzone`, `lucide-react`, `tailwind-merge`, `clsx`
   - UI framework: shadcn/ui (install via CLI)
   - Create folder structure:
     ```
     frontend/
     ├── src/
     │   ├── app/
     │   │   ├── layout.tsx            # Root layout with Clerk provider
     │   │   ├── page.tsx              # Landing / dashboard
     │   │   ├── sign-in/[[...sign-in]]/page.tsx
     │   │   ├── sign-up/[[...sign-up]]/page.tsx
     │   │   ├── cases/
     │   │   │   ├── page.tsx          # Cases list
     │   │   │   └── [id]/
     │   │   │       ├── page.tsx      # Case detail (chat + upload + summary)
     │   │   │       └── review/page.tsx  # Reviewer view
     │   │   └── admin/
     │   │       └── page.tsx          # Admin dashboard
     │   ├── components/
     │   │   ├── ui/                   # shadcn/ui components
     │   │   ├── chat/
     │   │   │   ├── ChatPanel.tsx     # Main chat interface
     │   │   │   ├── MessageBubble.tsx
     │   │   │   └── ChatInput.tsx
     │   │   ├── documents/
     │   │   │   ├── UploadZone.tsx    # Drag-and-drop upload
     │   │   │   ├── DocumentCard.tsx  # Shows extracted data + confidence
     │   │   │   └── FieldEditor.tsx   # Edit extracted values
     │   │   ├── tax/
     │   │   │   ├── TaxSummary.tsx    # Final tax breakdown
     │   │   │   ├── RefundBanner.tsx  # Refund/balance due highlight
     │   │   │   └── LineItemTable.tsx
     │   │   ├── review/
     │   │   │   ├── ReviewPanel.tsx
     │   │   │   └── ConfidenceBadge.tsx
     │   │   └── layout/
     │   │       ├── Sidebar.tsx
     │   │       ├── Header.tsx
     │   │       └── ProgressBar.tsx   # Tax prep progress indicator
     │   ├── lib/
     │   │   ├── api.ts               # Axios instance configured for backend
     │   │   └── utils.ts
     │   ├── hooks/
     │   │   ├── useCase.ts           # React Query hook for case data
     │   │   ├── useChat.ts           # Chat state management
     │   │   └── useDocuments.ts
     │   ├── stores/
     │   │   └── caseStore.ts         # Zustand store for active case
     │   └── types/
     │       ├── case.ts
     │       ├── document.ts
     │       ├── taxFacts.ts
     │       └── chat.ts
     ├── public/
     ├── next.config.ts
     ├── tailwind.config.ts
     └── package.json
     ```

4. **Database schema (Alembic migration)** — *depends on step 2*
   Define these tables:
   - `cases` — id (UUID), user_id, status (enum: intake/extracting/validating/computing/review/complete), tax_year, filing_status, created_at, updated_at
   - `documents` — id (UUID), case_id (FK), doc_type (enum: W2/1099_INT/1099_DIV/OTHER), file_path, file_name, file_size, mime_type, extracted_data (JSONB), evidence (JSONB with bboxes/confidence), status (enum: uploaded/processing/extracted/verified/error), created_at
   - `tax_facts` — id (UUID), case_id (FK), version (int, for tracking changes), facts_data (JSONB matching canonical TaxFacts schema), source_map (JSONB linking each fact to evidence), created_at
   - `computations` — id (UUID), case_id (FK), tax_facts_version (int), engine_name, engine_version, tax_year, input_payload (JSONB), output_payload (JSONB), created_at
   - `chat_messages` — id (UUID), case_id (FK), role (enum: user/assistant/system), content (text), structured_output (JSONB, nullable), created_at
   - `audit_logs` — id (UUID), case_id (FK, nullable), user_id, action (varchar), entity_type, entity_id, old_value (JSONB), new_value (JSONB), ip_address, created_at
   - `reviews` — id (UUID), case_id (FK), reviewer_id, decision (enum: approved/rejected/needs_changes), notes (text), created_at

5. **Docker Compose for local dev** — *parallel with step 4*
   Services: `postgres` (5432), `redis` (6379), `backend` (8000), `frontend` (3000)
   Environment variables template in `.env.example`

6. **Clerk auth integration** — *depends on steps 2, 3*
   - Backend: Clerk JWT verification middleware that validates `Authorization: Bearer <token>` on all API routes, extracts `user_id`, `email`, and `role` from claims
   - Frontend: `ClerkProvider` in root layout, `SignIn`/`SignUp` pages, `useAuth()` hook, middleware.ts to protect routes

7. **CI/CD setup** — *parallel with steps 4-6*
   - GitHub Actions workflow for: linting (ruff + eslint), type checking (mypy + tsc), tests (pytest + vitest), deploy (Vercel for frontend via Vercel GitHub integration, Railway for backend via railway CLI)

### Relevant files to create
- `backend/app/main.py` — FastAPI app factory with CORS, lifespan events, router includes
- `backend/app/config.py` — Pydantic BaseSettings loading from env vars (DATABASE_URL, OPENAI_API_KEY, CLERK_SECRET_KEY, etc.)
- `backend/app/database.py` — Async SQLAlchemy engine, sessionmaker, `get_db` dependency
- `backend/app/models/*.py` — All ORM models listed above
- `backend/app/auth/clerk.py` — Clerk JWT decode + verification dependency
- `frontend/src/app/layout.tsx` — Root layout with ClerkProvider
- `frontend/src/middleware.ts` — Clerk auth middleware
- `frontend/src/lib/api.ts` — Axios instance with Clerk token injection
- `docker-compose.yml` — Postgres + Redis + backend + frontend services

---

## Phase 2: Document Pipeline (Upload + Extraction)

**Goal**: Users can upload W-2 PDFs/images, system extracts structured data via GPT-4 Vision, user confirms/corrects.

### Steps

8. **File upload endpoint** — `POST /cases/{id}/documents`
   - Accept multipart file upload (PDF, PNG, JPG)
   - Validate file type and size (max 10MB)
   - Store file locally (abstract behind `StorageService` for later S3 migration)
   - Create `documents` DB record with status=`uploaded`
   - Emit audit log entry
   - Return document metadata

9. **GPT-4 Vision extraction service** — *depends on step 8*
   - In `document_service.py`, implement `extract_document(document_id)`:
     a. Load file from storage
     b. If PDF, convert pages to images (use `pdf2image` or `PyMuPDF`)
     c. Send image(s) to OpenAI GPT-4 Vision with a structured prompt:
        - System prompt: "You are a tax document extraction agent. Extract fields from this W-2 form into the exact JSON schema provided. Include confidence scores for each field. Do NOT compute or interpret tax implications."
        - Include the canonical W-2 extraction JSON schema (employer name, EIN, wages box 1, fed withheld box 2, SS wages box 3, SS tax box 4, Medicare wages box 5, Medicare tax box 6, state, state wages, state tax withheld, employee name, SSN last 4)
        - Use `response_format: { type: "json_object" }` for structured output
     d. Parse response, validate against schema
     e. Store `extracted_data` and `evidence` (confidence scores per field) on document record
     f. Update document status to `extracted`
     g. Emit audit log

10. **Extraction API endpoint** — `POST /cases/{id}/extract` — *depends on step 9*
    - Triggers extraction for all unprocessed documents in the case
    - Returns extracted fields with confidence scores

11. **Frontend: Document upload UI** — *parallel with steps 8-10*
    - `UploadZone.tsx`: drag-and-drop with `react-dropzone`, file type validation, upload progress
    - `DocumentCard.tsx`: displays extracted data with confidence badges (green >0.95, yellow >0.8, red <0.8)
    - `FieldEditor.tsx`: inline editing for user corrections, tracks which fields were manually changed

12. **Frontend: Document review flow** — *depends on step 11*
    - After upload + extraction, show extracted values for confirmation
    - User can click to edit any field
    - "Confirm All" button saves verified facts
    - Changes are sent to `PATCH /cases/{id}/documents/{doc_id}` endpoint

### Relevant files
- `backend/app/api/documents.py` — Upload endpoint
- `backend/app/api/extraction.py` — Extraction trigger endpoint
- `backend/app/services/document_service.py` — GPT-4V extraction logic with structured prompt and schema enforcement
- `backend/app/utils/storage.py` — `StorageService` class (local filesystem for now)
- `frontend/src/components/documents/UploadZone.tsx`
- `frontend/src/components/documents/DocumentCard.tsx`
- `frontend/src/components/documents/FieldEditor.tsx`

---

## Phase 3: AI Interview Orchestrator

**Goal**: LLM-driven conversational interview collects missing tax information (filing status, dependents, additional docs), outputting structured TaxFacts.

### Steps

13. **Interview service** — `backend/app/services/interview_service.py`
    - Maintains interview state machine: `greeting → filing_status → dependents → income_review → deductions → missing_docs → complete`
    - Each state has:
      - Required facts to collect
      - Validation rules
      - Prompt template for the LLM
    - `get_next_question(case_id)`: checks what facts are missing, constructs an OpenAI chat completion call with:
      - System prompt: "You are a tax preparation assistant. Ask one question at a time to collect the following missing info: {missing_fields}. Be conversational and friendly. Output both a user-facing message AND structured data in JSON. NEVER compute taxes or make eligibility determinations."
      - Chat history from `chat_messages` table
      - Current known facts from `tax_facts`
    - `process_answer(case_id, user_message)`: sends user answer to LLM with extraction prompt, extracts structured facts, validates, updates `tax_facts`, returns next question or completion signal

14. **Chat API endpoint** — `POST /cases/{id}/chat`
    - Request: `{ message: string }`
    - Calls `interview_service.process_answer()` then `get_next_question()`
    - Response: `{ assistant_message: string, structured_update: object | null, progress: { current_step: string, completion_pct: number }, unresolved_questions: string[] }`
    - Stores both user and assistant messages in `chat_messages`

15. **Normalize endpoint** — `POST /cases/{id}/normalize` — *depends on steps 9, 13*
    - Merges document-extracted data + interview answers into canonical `TaxFacts`
    - Resolves conflicts (e.g., doc says $72,400 wages, user typed $7,240 → flag)
    - Returns `{ tax_facts, unresolved_questions, validation_errors }`

16. **Frontend: Chat panel** — *parallel with steps 13-15*
    - `ChatPanel.tsx`: scrollable message list, input box, typing indicator
    - `MessageBubble.tsx`: different styles for user/assistant, assistant messages can include structured data previews
    - `ChatInput.tsx`: text input + send button, disabled while waiting for response
    - Shows progress bar based on interview state
    - Integrates with document upload (assistant can say "Please upload your W-2")

### Relevant files
- `backend/app/services/interview_service.py` — Interview state machine + LLM orchestration
- `backend/app/api/chat.py` — Chat endpoint
- `backend/app/api/intake.py` — Normalize endpoint
- `backend/app/schemas/intake.py` — TaxFacts canonical schema (Pydantic model)
- `frontend/src/components/chat/ChatPanel.tsx`
- `frontend/src/components/chat/MessageBubble.tsx`
- `frontend/src/components/chat/ChatInput.tsx`
- `frontend/src/hooks/useChat.ts`

---

## Phase 4: Tax Engine Integration

**Goal**: Compute federal tax using Tax-Calculator from validated TaxFacts, return line-item results.

### Steps

17. **Engine adapter service** — `backend/app/services/engine_adapter.py`
    - `TaxCalcAdapter` class:
      - `map_facts_to_engine_input(tax_facts: TaxFacts) -> dict`: Maps canonical TaxFacts to Tax-Calculator variables:
        - `RECID` → 1 (single record)
        - `MARS` → filing status code (1=Single, 2=MFJ, 3=MFS, 4=HOH, 5=QSS)
        - `e00200` → total W-2 wages
        - `n24` → count of dependents under 17 (CTC eligible, for future use)
        - `nu06` → count of dependents under 6 (for future use)
        - Other inputs as needed
      - `compute(tax_facts: TaxFacts, tax_year: int) -> ComputationResult`:
        a. Map facts to engine input
        b. Create Tax-Calculator `Records` object from input DataFrame
        c. Create `Policy` object for the target `tax_year`
        d. Create `Calculator` and call `calc_all()`
        e. Extract key outputs: `iitax` (income tax), `payrolltax`, `combined`, standard deduction used, taxable income, etc.
        f. Build result with line items, engine version, input snapshot
      - `get_engine_version() -> str`: Return Tax-Calculator version for audit

18. **Compute API endpoint** — `POST /cases/{id}/compute` — *depends on step 17*
    - Validates that all required fields are present and no critical conflicts remain
    - Calls `engine_adapter.compute()`
    - Stores result in `computations` table
    - Returns: tax results, line items, refund/balance estimate (withheld - tax owed), engine metadata

19. **Refund/balance calculation** — *depends on step 18*
    - Tax-Calculator computes tax liability but may not handle withholding credits directly
    - Add simple post-processing: `refund = fed_income_tax_withheld - income_tax_liability`
    - This is a simple subtraction, not tax law — safe to do outside engine

20. **Explanation service** — `backend/app/services/explanation_service.py` — *depends on step 18*
    - Takes computation results, sends to OpenAI with prompt:
      "Given these ALREADY COMPUTED tax results, explain them in plain language. Do NOT recalculate anything. Explain WHY the refund/balance is what it is."
    - Returns plain-language explanation paragraphs
    - Cached per computation (same inputs = same explanation)

### Relevant files
- `backend/app/services/engine_adapter.py` — TaxCalcAdapter class with mapping + computation
- `backend/app/api/computation.py` — Compute endpoint
- `backend/app/services/explanation_service.py` — LLM-based explanation of results
- `backend/app/schemas/computation.py` — ComputationResult Pydantic model

---

## Phase 5: Validation Layer

**Goal**: Enforce data integrity rules between AI extraction and tax computation.

### Steps

21. **Validation service** — `backend/app/services/validation_service.py`
    - Rules engine (simple Python, no framework needed for MVP):
      - Required fields check: filing_status, tax_year, at least one income source
      - Filing status must be one of: SINGLE, MFJ, MFS, HOH, QSS
      - W-2 Box 2 withholding ≤ W-2 Box 1 wages (warn if > 50% ratio)
      - All monetary values ≥ 0
      - SSN format validation (last 4 only in MVP)
      - Dependent count reconciliation
      - Document extraction confidence threshold (warn if any field < 0.8)
    - Returns: `{ valid: bool, errors: ValidationError[], warnings: ValidationWarning[] }`
    - Errors block computation; warnings are shown but don't block

22. **Validate API endpoint** — `POST /cases/{id}/validate` — *depends on step 21*
    - Runs validation on current tax_facts
    - Returns errors and warnings
    - Auto-called before compute

23. **Frontend: Validation display** — *depends on step 22*
    - Show errors as red alerts (must fix before computing)
    - Show warnings as yellow alerts (can proceed but should review)
    - Link each error/warning to the relevant field for quick editing

### Relevant files
- `backend/app/services/validation_service.py` — Rule-based validation engine
- `backend/app/api/validation.py` — Validate endpoint
- `backend/app/schemas/tax_facts.py` — TaxFacts Pydantic model with field validators

---

## Phase 6: Results, Review & Audit

**Goal**: Display tax results, enable internal review workflow, maintain complete audit trail.

### Steps

24. **Tax summary page** — frontend
    - `TaxSummary.tsx`: clean dashboard showing income, deductions, tax owed, withheld, refund/balance
    - `RefundBanner.tsx`: prominent green (refund) or red (balance due) banner
    - `LineItemTable.tsx`: detailed line-by-line breakdown matching Form 1040 structure
    - "Explain this" button triggers explanation service
    - "Download Summary" button generates PDF (use `@react-pdf/renderer` or server-side generation)

25. **Review workflow** — *depends on step 24*
    - Backend: `POST /cases/{id}/review` — reviewer submits decision (approved/rejected/needs_changes) with notes
    - Frontend: `ReviewPanel.tsx` — shows all case data, extracted documents, chat history, computation results side-by-side. Reviewer can approve or send back with notes
    - Case status flow: `intake → extracting → validating → computing → review → complete`

26. **Audit trail service** — *parallel with all above steps (integrated throughout)*
    - `audit_service.py`: `log_event(case_id, user_id, action, entity_type, entity_id, old_value, new_value)`
    - Called from every state change: document upload, extraction, fact update, computation, review decision
    - Audit logs are immutable (INSERT only, no UPDATE/DELETE)
    - Admin can view audit history per case

27. **Summary API** — `GET /cases/{id}/summary`
    - Returns complete case overview: facts, documents, computation results, review status, audit history
    - Powers the tax summary page and review panel

### Relevant files
- `frontend/src/components/tax/TaxSummary.tsx`
- `frontend/src/components/tax/RefundBanner.tsx`
- `frontend/src/components/tax/LineItemTable.tsx`
- `frontend/src/components/review/ReviewPanel.tsx`
- `backend/app/services/audit_service.py`
- `backend/app/api/review.py`
- `backend/app/api/summary.py`

---

## Phase 7: Security & Deployment

**Goal**: Harden security, deploy to production environments, set up monitoring.

### Steps

28. **Security hardening**
    - Encrypt all data at rest (PostgreSQL with encryption, file storage encryption)
    - HTTPS everywhere (Vercel and Railway handle TLS)
    - SSN masking in UI and logs (show only last 4)
    - Rate limiting on API endpoints (use `slowapi`)
    - CORS locked to frontend domain only
    - Input sanitization on all user inputs
    - File upload validation (magic bytes check, not just extension)
    - Environment variable management (no secrets in code)

29. **Deployment setup**
    - Frontend: Connect GitHub repo to Vercel, configure environment variables (Clerk keys, API URL)
    - Backend: Deploy to Railway, configure PostgreSQL addon, environment variables (DATABASE_URL, OPENAI_API_KEY, CLERK_SECRET_KEY)
    - Set up separate staging and production environments
    - Configure Vercel preview deployments for PRs

30. **Monitoring & error tracking**
    - Backend: structured logging with `structlog`, error tracking with Sentry
    - Frontend: Sentry for client-side errors
    - Health check endpoint: `GET /health`

---

## Verification

1. **Unit tests**: Test `engine_adapter.py` mapping with known W-2 inputs → verify Tax-Calculator produces expected tax liability for known scenarios (e.g., $72,400 wages, Single filer, standard deduction → expected taxable income and tax)
2. **Integration tests**: Upload a sample W-2 image → verify extraction → verify interview fills gaps → verify computation matches hand-calculated result
3. **E2E test**: Full flow from login → create case → upload W-2 → chat interview → compute → view summary → reviewer approves
4. **Validation tests**: Submit intentionally bad data (negative wages, missing filing status, conflicting doc/user values) → verify errors are caught
5. **Security tests**: Verify unauthenticated requests are rejected, verify one user can't access another's case, verify SSN is masked in API responses and logs
6. **Tax accuracy tests**: Use IRS tax tables for TY2025 to verify computation results for multiple scenarios:
   - Single, $50K wages, standard deduction
   - MFJ, $100K wages, standard deduction
   - HOH, $75K wages, 1 dependent, standard deduction

---

## Decisions

- **Tax-Calculator** chosen over PolicyEngine/OpenFisca due to CC0/public-domain license (no AGPL concerns for future commercialization)
- **GPT-4 Vision** for OCR instead of Tesseract — simpler for MVP, higher accuracy on varied W-2 formats, one less dependency
- **Clerk** for auth — minimal setup, works well with both Next.js and FastAPI, free tier sufficient for internal use
- **Split deployment** — Vercel for Next.js (optimal), Railway for FastAPI + PostgreSQL (good Python support, managed Postgres)
- **MVP scope explicitly excludes**: state taxes, 1099s, itemized deductions, credits (including CTC), e-filing, public users, Schedule C

## Further Considerations

1. **Tax-Calculator TY2025 readiness**: Tax-Calculator may not have TY2025 parameters yet (its `LAST_KNOWN_YEAR` was 2026 as of the planning docs). Need to verify during implementation. If not available, fall back to TY2024. *Recommendation: Check during Phase 4 and adapt.*
2. **File storage migration**: MVP uses local file storage. Before production deployment, migrate to S3-compatible storage (Railway supports volume mounts, or use AWS S3 / Cloudflare R2). *Recommendation: Abstract behind StorageService from day one (already in plan).*
3. **Redis dependency**: Redis is listed for job queues / caching. For MVP, document extraction can run synchronously (GPT-4V calls take 5-15s). *Recommendation: Skip Redis for MVP, add when you need background job processing.*
