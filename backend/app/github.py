"""GitHub API client."""
import os
import requests
from typing import Optional
from app.config import settings


class GitHubClient:
    """Speak to GitHub REST API."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.base = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base}{path}"
        r = requests.request(method, url, headers=self.headers, **kwargs)
        r.raise_for_status()
        return r.json()

    def get_repo(self, owner: str, repo: str) -> dict:
        return self._request("GET", f"/repos/{owner}/{repo}")

    def get_issue(self, owner: str, repo: str, number: int) -> dict:
        return self._request("GET", f"/repos/{owner}/{repo}/issues/{number}")

    def create_comment(self, owner: str, repo: str, number: int, body: str) -> dict:
        return self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{number}/comments",
            json={"body": body},
        )

    def get_pull_request(self, owner: str, repo: str, number: int) -> dict:
        return self._request("GET", f"/repos/{owner}/{repo}/pulls/{number}")

    def get_pr_files(self, owner: str, repo: str, number: int) -> list:
        return self._request("GET", f"/repos/{owner}/{repo}/pulls/{number}/files")

    def create_pr_review(
        self, owner: str, repo: str, number: int, body: str, event: str = "COMMENT"
    ):
        return self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls/{number}/reviews",
            json={"body": body, "event": event},
        )

    def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        try:
            data = self._request("GET", f"/repos/{owner}/{repo}/contents/{path}")
            import base64

            return base64.b64decode(data["content"]).decode()
        except Exception:
            return None
