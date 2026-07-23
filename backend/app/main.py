"""RepoGuardian - AI-powered open-source maintainer."""
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware

  from app.config import settings
  from app.webhook import router as webhook_router
  from app.database import init_db

  app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  app.include_router(webhook_router)


  @app.on_event("startup")
  async def startup():
      await init_db()


  @app.get("/")
  def root():
      return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status":
  "running"}


  @app.get("/health")
  def health():
      return {"status": "ok"}
