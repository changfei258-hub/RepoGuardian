\"\"\"GitHub webhook receiver - handles issues, PRs, and auto-replies.\"\"\"
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Request, HTTPException

from app.ai import analyze_issue, review_pr
from app.github import GitHubClient
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    \"\"\"Verify that the webhook payload was signed by GitHub.\"\"\"
    if not settings.GITHUB_WEBHOOK_SECRET:
        logger.warning("Webhook secret not configured - skipping signature check")
        return True
    hash_type, sig = signature_header.split("=", 1)
    expected = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        payload_body,
        getattr(hashlib, hash_type),
    ).hexdigest()
    return hmac.compare_digest(expected, sig)


@router.post("/webhook")
  async def webhook(request: Request, db: AsyncSession = Depends(get_db)):
      # Read body
      body = await request.body()
      raw = body.decode("utf-8", errors="replace") if body else ""

      sig = request.headers.get("x-hub-signature-256", "")
      event = request.headers.get("x-github-event", "")

      print(f"Webhook received: event={event}, body_len={len(body)}, sig={bool(sig)}")

      if not body:
          raise HTTPException(400, f"Empty body (event={event})")

      if not verify_signature(body, sig):
          raise HTTPException(403, "Invalid signature")

      try:
          data = json.loads(body)
      except json.JSONDecodeError:
          raise HTTPException(400, f"Invalid JSON: {raw[:200]}")

      repo_full = data.get("repository", {}).get("full_name", "")
      owner, repo_name = repo_full.split("/") if "/" in repo_full else ("", "")

      if event == "issues" and data.get("action") in ("opened", "reopened"):
          await handle_issue(data, owner, repo_name, db)
      elif event == "issue_comment" and data.get("action") == "created":
          await handle_comment(data, owner, repo_name)
      elif event == "pull_request" and data.get("action") in ("opened", "reopened",
  "synchronize"):
          await handle_pr(data, owner, repo_name, db)

      return {"received": True}
