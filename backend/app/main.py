from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if needed (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title="BooksInsight Tax API",
    version="0.1.0",
    description="AI-Assisted Tax Preparation System",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.api.cases import router as cases_router
from app.api.documents import router as documents_router
from app.api.extraction import router as extraction_router
from app.api.chat import router as chat_router
from app.api.intake import router as intake_router
from app.api.validation import router as validation_router
from app.api.computation import router as computation_router
from app.api.review import router as review_router

app.include_router(cases_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(extraction_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(intake_router, prefix="/api")
app.include_router(validation_router, prefix="/api")
app.include_router(computation_router, prefix="/api")
app.include_router(review_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
