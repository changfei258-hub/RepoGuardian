"""GitHub webhook handler — the brain of RepoGuardian."""
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
    """Verify GitHub webhook signature."""
    if not settings.GITHUB_WEBHOOK_SECRET:
        return True  # skip check in dev
    expected = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


@router.post("/webhook")
async def webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    sig = request.headers.get("x-hub-signature-256", "")
    event = request.headers.get("x-github-event", "")

    if not verify_signature(body, sig):
        raise HTTPException(403, "Invalid signature")

    data = json.loads(body)
    repo_full = data.get("repository", {}).get("full_name", "")
    owner, repo_name = repo_full.split("/") if "/" in repo_full else ("", "")

    if event == "issues" and data.get("action") in ("opened", "reopened"):
        await handle_issue(data, owner, repo_name, db)

    elif event == "issue_comment" and data.get("action") == "created":
        await handle_comment(data, owner, repo_name)
    elif event == "pull_request" and data.get("action") in (
        "opened",
        "reopened",
        "synchronize",
    ):
        await handle_pr(data, owner, repo_name, db)

    return {"received": True}


async def handle_issue(data: dict, owner: str, repo: str, db: AsyncSession):
    """Analyze new issue + auto-reply."""
    gh = GitHubClient(owner, repo)
    issue = data["issue"]
    number = issue["number"]
    title = issue["title"]
    body = issue.get("body", "") or ""

    result = analyze_issue(title, body)
    gh.create_comment(owner, repo, number, result.get("answer", "Thanks, we'll review this."))

    # Save to DB
    result_obj = await db.execute(
        select(Repository).where(Repository.full_name == f"{owner}/{repo}")
    )
    repo_obj = result_obj.scalar_one_or_none()
    if repo_obj:
        db.add(
            Issue(
                repo_id=repo_obj.id,
                issue_number=number,
                title=title,
                body=body,
                category=result.get("category", ""),
                priority=result.get("priority", ""),
                ai_reply=result.get("answer", ""),
                is_duplicate=result.get("is_duplicate", False),
            )
        )
        await db.commit()


async def handle_comment(data: dict, owner: str, repo: str):
    """Check if comment needs AI response."""
    gh = GitHubClient(owner, repo)
    comment = data["comment"]
    text = comment.get("body", "")
    if "@repoguardian" in text.lower():
        gh.create_comment(
            owner,
            repo,
            data["issue"]["number"],
            "I'm looking into this! 🔍",
        )


async def handle_pr(data: dict, owner: str, repo: str, db: AsyncSession):
    """Review pull request."""
    gh = GitHubClient(owner, repo)
    pr = data["pull_request"]
    number = pr["number"]
    title = pr["title"]
    body = pr.get("body", "") or ""

    # Get diff
    files = gh.get_pr_files(owner, repo, number)
    diff_lines = []
    for f in files[:10]:  # limit to 10 files
        patch = f.get("patch", "")
        diff_lines.append(f"--- {f['filename']}\n{patch}")

    if not diff_lines:
        return

    result = review_pr("\n".join(diff_lines), title, body)
    gh.create_pr_review(
        owner,
        repo,
        number,
        result.get("review_body", "Reviewed by RepoGuardian."),
        "COMMENT",
    )
