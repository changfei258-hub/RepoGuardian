"""RepoGuardian configuration."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)


class Settings:
    APP_NAME: str = "RepoGuardian"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # GitHub App
    GITHUB_APP_ID: str = os.getenv("APP_ID", "")
    GITHUB_PRIVATE_KEY_PATH: str = os.getenv("GITHUB_PRIVATE_KEY_PATH", "github-private-key.pem")
    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")

    @property
    def github_private_key(self) -> str:
        """Read private key — first try env var (Render), then file (local)."""
        # 1) Try env var (Render deploys use this)
         from_env = os.getenv("GITHUB_PRIVATE_KEY")
  if from_env:
      return from_env.replace("\\n", "\n").strip('"').strip("'")
        # 2) Try file (local dev)
        path = self.GITHUB_PRIVATE_KEY_PATH
        if not os.path.isabs(path):
            path = os.path.join(os.path.dirname(__file__), "..", path)
        try:
            with open(path) as f:
                return f.read()
        except FileNotFoundError:
            return ""

    # AI (OpenAI / compatible)
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4o-mini")
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./repoguardian.db",
    )

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
