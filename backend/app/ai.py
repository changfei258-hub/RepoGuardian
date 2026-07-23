"""AI issue & PR analysis."""
from openai import OpenAI
from app.config import settings

client = OpenAI(
    api_key=settings.AI_API_KEY,
    base_url=settings.AI_BASE_URL,
)

ISSUE_ANALYSIS_PROMPT = """You are RepoGuardian, an AI open-source maintainer.

Analyze the following GitHub issue. Return a valid JSON object only:

{
  "category": "bug" | "feature" | "question" | "documentation" | "other",
  "priority": "critical" | "high" | "medium" | "low",
  "is_duplicate": false,
  "summary": "One-sentence summary of the issue",
  "answer": "A helpful, friendly response to the issue author. Be concise but complete."
}
"""

PR_REVIEW_PROMPT = """You are RepoGuardian, an AI code reviewer.

Review the following pull request changes. Return JSON:

{
  "summary": "What this PR does in one sentence",
  "issues": [
    {
      "file": "path/to/file.py",
      "line": 1,
      "severity": "error" | "warning" | "nitpick",
      "message": "Description of the issue"
    }
  ],
  "overall_score": "approve" | "changes_requested" | "comment",
  "review_body": "A thorough but kind code review comment for the PR author."
}
"""


def analyze_issue(title: str, body: str) -> dict:
    """Send issue to AI for analysis."""
    text = f"## Title\n{title}\n\n## Body\n{body}" if body else f"## Title\n{title}"
    resp = client.chat.completions.create(
        model=settings.AI_MODEL,
        messages=[
            {"role": "system", "content": ISSUE_ANALYSIS_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return _parse_json(resp.choices[0].message.content)


def review_pr(diff_text: str, title: str, body: str = "") -> dict:
    """Review a pull request via AI."""
    text = f"## PR Title\n{title}\n\n## Description\n{body}\n\n## Diff\n```diff\n{diff_text[:8000]}\n```"
    resp = client.chat.completions.create(
        model=settings.AI_MODEL,
        messages=[
            {"role": "system", "content": PR_REVIEW_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return _parse_json(resp.choices[0].message.content)


def _parse_json(raw: str) -> dict:
    """Safely parse AI JSON response."""
    import json, re

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown block
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        return {"category": "other", "priority": "medium", "summary": "", "answer": raw}
