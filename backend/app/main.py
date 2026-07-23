"""RepoGuardian — AI-powered open-source maintainer."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.webhook import router as webhook_router
from app.database import init_db

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router, prefix="", tags=["webhook"])


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug")
def debug():
    """Debug endpoint — check config without exposing secrets."""
    import os
    key_from_env = os.getenv("GITHUB_PRIVATE_KEY", "")
    return {
        "app_id": settings.GITHUB_APP_ID,
        "key_env_var_exists": bool(key_from_env),
        "key_env_var_length": len(key_from_env),
        "key_env_var_starts_with": key_from_env[:50] if key_from_env else "N/A",
        "ai_key_configured": bool(settings.AI_API_KEY),
        "ai_model": settings.AI_MODEL,
        "db_url": settings.DATABASE_URL,
    }
