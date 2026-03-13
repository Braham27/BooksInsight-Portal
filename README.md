# BooksInsight Portal — AI-Assisted Tax Preparation System

US-only, internal AI-assisted tax preparation MVP.

**Core rule**: LLMs never compute taxes. They handle intake, document understanding, and conversation. Tax-Calculator handles all tax math.

## Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Python FastAPI, SQLAlchemy (async), Alembic
- **Database**: PostgreSQL
- **Auth**: Clerk
- **AI**: OpenAI GPT-4 / GPT-4 Vision
- **Tax Engine**: PSLmodels Tax-Calculator (CC0 license)
- **Deployment**: Vercel (frontend) + Railway (backend + DB)

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Option 1: Docker Compose

```bash
cp .env.example .env
# Fill in your API keys in .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

### Option 2: Manual Setup

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── api/      # Route handlers
│   │   ├── auth/     # Clerk JWT verification
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── schemas/  # Pydantic request/response models
│   │   ├── services/ # Business logic
│   │   └── utils/    # Storage, helpers
│   ├── alembic/      # Database migrations
│   └── tests/
├── frontend/         # Next.js TypeScript frontend
│   └── src/
│       ├── app/      # App Router pages
│       ├── components/
│       ├── hooks/
│       ├── lib/
│       ├── stores/
│       └── types/
├── docs/             # Architecture documents
└── docker-compose.yml
```

## Architecture

```
User → Chat UI + Document Upload
         ↓
   Orchestrator API (FastAPI)
         ↓
   Document Pipeline → Structured Tax Facts → Validation Layer
                                    ↓
                          Tax Engine Adapter (Tax-Calculator)
                                    ↓
                       Results + Explanations + Audit Trail
```

## MVP Scope

- US federal only (TY2025)
- W-2 income only
- Standard deduction only
- No e-file
- Internal use only

## Environment Variables

See `.env.example` for all required configuration.
