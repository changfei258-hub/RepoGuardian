"""Database models and setup."""
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Handle SQLite vs PostgreSQL
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///"),
        echo=settings.DEBUG,
    )
else:
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


# ── Models ─────────────────────────────────────────
class Repository(Base):
    __tablename__ = "repositories"

    id = sa.Column(sa.Integer, primary_key=True)
    github_id = sa.Column(sa.Integer, unique=True, nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    owner = sa.Column(sa.String(255), nullable=False)
    full_name = sa.Column(sa.String(510), unique=True, nullable=False)


class Issue(Base):
    __tablename__ = "issues"

    id = sa.Column(sa.Integer, primary_key=True)
    repo_id = sa.Column(sa.Integer, sa.ForeignKey("repositories.id"))
    issue_number = sa.Column(sa.Integer, nullable=False)
    title = sa.Column(sa.Text, nullable=False)
    body = sa.Column(sa.Text, default="")
    category = sa.Column(sa.String(50), default="")
    priority = sa.Column(sa.String(20), default="")
    ai_reply = sa.Column(sa.Text, default="")
    is_duplicate = sa.Column(sa.Boolean, default=False)
    created_at = sa.Column(sa.DateTime, server_default=sa.func.now())


# ── Init ────────────────────────────────────────────
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
