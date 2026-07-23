"""GitHub API client — supports GitHub App auth (JWT + installation tokens)."""
import os
import time
import requests
import jwt
from typing import Optional
from app.config import settings


class GitHubClient:
    """Speak to GitHub REST API via GitHub App authentication."""

    def __init__(self, owner: str = "", repo: str = ""):
        self.base = "https://api.github.com"
        self.owner = owner
        self.repo = repo
        self._token = None
        self._token_expires = 0

    # ── JWT (App-level auth, used to get installation token) ──────────
    def _generate_jwt(self) -> str:
        """Create a JWT signed with the app's private key."""
        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + 600,
            "iss": settings.GITHUB_APP_ID,
        }
        key = settings.github_private_key
        if not key:
            raise RuntimeError("GitHub private key not found")
        return jwt.encode(payload, key, algorithm="RS256")

    # ── Installation token (actual API credential) ───────────────────
    def _get_installation_token(self) -> str:
        """Get an installation access token for the target repo."""
        if self._token and time.time() < self._token_expires - 60:
            return self._token

        jwt_token = self._generate_jwt()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
        }

        # Find installation ID for this repo
        url = f"{self.base}/repos/{self.owner}/{self.repo}/installation"
        r = requests.get(url, headers=headers, verify=False)
        r.raise_for_status()
        installation_id = r.json()["id"]

        # Get installation token
        url = f"{self.base}/app/installations/{installation_id}/access_tokens"
        r = requests.post(url, headers=headers, verify=False)
        r.raise_for_status()
        data = r.json()
        self._token = data["token"]
        self._token_expires = time.time() + 3600
        return self._token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self._get_installation_token()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    # ── API methods ──────────────────────────────────────────────────
    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base}{path}"
        kwargs.setdefault("verify", False)
        r = requests.request(method, url, headers=self._headers(), **kwargs)
        r.raise_for_status()
        return r.json() if r.content else {}

    def get_repo(self, owner: str = "", repo: str = "") -> dict:
        o = owner or self.owner
        r = repo or self.repo
        return self._request("GET", f"/repos/{o}/{r}")

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
