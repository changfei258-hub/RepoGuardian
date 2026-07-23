"""GitHub webhook handler - RepoGuardian."""
  import json
  import hmac
  import hashlib
  from fastapi import APIRouter, Request, HTTPException, Depends
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select

  from app.config import settings
  from app.github import GitHubClient
  from app.ai import analyze_issue, review_pr
  from app.database import get_db, Repository, Issue

  router = APIRouter()


  def verify_signature(payload: bytes, signature: str) -> bool:
      if not settings.GITHUB_WEBHOOK_SECRET:
          return True
      expected = hmac.new(
          settings.GITHUB_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
      ).hexdigest()
      return hmac.compare_digest(f"sha256={expected}", signature)


  @router.post("/webhook")
  async def webhook(request: Request, db: AsyncSession = Depends(get_db)):
      body = await request.body()
      sig = request.headers.get("x-hub-signature-256", "")
      event = request.headers.get("x-github-event", "")

      if not body:
          raise HTTPException(400, "Empty body")

      if not verify_signature(body, sig):
          raise HTTPException(403, "Invalid signature")

      data = json.loads(body.decode())
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


  async def handle_issue(data, owner, repo, db):
      gh = GitHubClient(owner, repo)
      issue = data["issue"]
      result = analyze_issue(issue["title"], issue.get("body", "") or "")
      gh.create_comment(owner, repo, issue["number"], result.get("answer", "Thanks!"))
      result_obj = await db.execute(
          select(Repository).where(Repository.full_name == f"{owner}/{repo}")
      )
      repo_obj = result_obj.scalar_one_or_none()
      if repo_obj:
          db.add(Issue(
              repo_id=repo_obj.id, issue_number=issue["number"],
              title=issue["title"], body=issue.get("body", ""),
              category=result.get("category", ""), priority=result.get("priority", ""),
              ai_reply=result.get("answer", ""),
  is_duplicate=result.get("is_duplicate", False),
          ))
          await db.commit()


  async def handle_comment(data, owner, repo):
      gh = GitHubClient(owner, repo)
      text = data["comment"].get("body", "")
      if "@repoguardian" in text.lower():
          gh.create_comment(owner, repo, data["issue"]["number"], "Looking into this!")


  async def handle_pr(data, owner, repo, db):
      gh = GitHubClient(owner, repo)
      pr = data["pull_request"]
      files = gh.get_pr_files(owner, repo, pr["number"])
      diffs = [f"--- {f['filename']}\n{f.get('patch', '')}" for f in files[:10]]
      if not diffs:
          return
      result = review_pr("\n".join(diffs), pr["title"], pr.get("body", "") or "")
      gh.create_pr_review(owner, repo, pr["number"], result.get("review_body", ""),
  "COMMENT")
