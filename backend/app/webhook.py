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
async def webhook(request: Request):
    \"\"\"Receive GitHub webhook events and process them.\"\"\"
    # Read raw body - use stream() to avoid middleware interference
    body = await request.body()
    if not body:
        logger.warning("Empty request body received")
        raise HTTPException(status_code=400, detail="Empty body")

    # Verify signature
    sig = request.headers.get("x-hub-signature-256") or request.headers.get("x-hub-signature")
    if sig and not verify_signature(body, sig):
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Parse event
    event = request.headers.get("x-github-event", "")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse webhook body: %s", e)
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    logger.info("Received event: %s | action: %s", event, payload.get("action"))

    if event == "ping":
        return {"msg": "pong"}

    if event == "issues" and payload.get("action") in ("opened", "reopened"):
        await handle_issue_opened(payload)
        return {"status": "ok", "action": "issue_analyzed"}

    if event == "issue_comment" and payload.get("action") == "created":
        await handle_issue_comment(payload)
        return {"status": "ok", "action": "comment_processed"}

    if event == "pull_request" and payload.get("action") in ("opened", "reopened", "synchronize"):
        await handle_pr_opened(payload)
        return {"status": "ok", "action": "pr_reviewed"}

    return {"status": "skipped", "event": event, "action": payload.get("action")}


async def handle_issue_opened(payload: dict):
    \"\"\"Analyze a new issue and post an AI-generated reply.\"\"\"
    repo_full = payload["repository"]["full_name"]
    owner, repo = repo_full.split("/")
    issue = payload["issue"]
    number = issue["number"]
    title = issue.get("title", "")
    body_text = issue.get("body", "") or ""

    logger.info("Analyzing issue #%d in %s", number, repo_full)

    try:
        result = analyze_issue(title, body_text)
    except Exception as e:
        logger.error("AI analysis failed for issue #%d: %s", number, e)
        return

    answer = result.get("answer", "")
    if not answer:
        logger.info("No auto-reply for issue #%d", number)
        return

    try:
        client = GitHubClient(owner=owner, repo=repo)
        client.create_comment(owner, repo, number, answer)
        logger.info("Posted reply to issue #%d", number)
    except Exception as e:
        logger.error("Failed to post reply to issue #%d: %s", number, e)


async def handle_issue_comment(payload: dict):
    \"\"\"Reply to comments that @mention the bot.\"\"\"
    repo_full = payload["repository"]["full_name"]
    owner, repo = repo_full.split("/")
    comment = payload["comment"]
    issue = payload["issue"]
    comment_body = comment.get("body", "")
    number = issue["number"]

    if not comment_body or ("@RepoGuardian" not in comment_body and "?" not in comment_body):
        return

    logger.info("Analyzing comment on issue #%d", number)

    try:
        result = analyze_issue(issue.get("title", ""), comment_body)
    except Exception as e:
        logger.error("AI analysis failed for comment on #%d: %s", number, e)
        return

    answer = result.get("answer", "")
    if not answer:
        return

    try:
        client = GitHubClient(owner=owner, repo=repo)
        client.create_comment(owner, repo, number, answer)
        logger.info("Posted reply to comment on issue #%d", number)
    except Exception as e:
        logger.error("Failed to post reply on #%d: %s", number, e)


async def handle_pr_opened(payload: dict):
    \"\"\"Review a newly opened pull request.\"\"\"
    repo_full = payload["repository"]["full_name"]
    owner, repo = repo_full.split("/")
    pr = payload["pull_request"]
    number = pr["number"]
    title = pr.get("title", "")
    body_text = pr.get("body", "") or ""

    logger.info("Reviewing PR #%d in %s", number, repo_full)

    try:
        client = GitHubClient(owner=owner, repo=repo)
        files = client.get_pr_files(owner, repo, number)
    except Exception as e:
        logger.error("Failed to fetch PR #%d files: %s", number, e)
        return

    diff_lines = []
    for f in files:
        filename = f.get("filename", "unknown")
        patch = f.get("patch", "")
        status = f.get("status", "modified")
        diff_lines.append(f"File: {filename} ({status})")
        if patch:
            diff_lines.append(patch[:2000])
    diff_text = "\n".join(diff_lines)

    if not diff_text:
        logger.info("No diff content for PR #%d, skipping review", number)
        return

    try:
        result = review_pr(diff_text, title, body_text)
    except Exception as e:
        logger.error("AI review failed for PR #%d: %s", number, e)
        return

    review_body = result.get("review_body", "")
    if not review_body:
        return

    try:
        client.create_pr_review(owner, repo, number, review_body)
        logger.info("Posted review on PR #%d", number)
    except Exception as e:
        logger.error("Failed to post review on PR #%d: %s", number, e)