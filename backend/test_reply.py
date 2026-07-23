"""Test replying to Issue #3."""
import sys, jwt, time, requests, urllib3
urllib3.disable_warnings()
sys.path.insert(0, '.')
from app.config import settings
from app.ai import analyze_issue

# Get installation token
key = settings.github_private_key
payload = {"iat": int(time.time())-60, "exp": int(time.time())+600, "iss": "4372444"}
token = jwt.encode(payload, key, algorithm="RS256")
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

r = requests.get("https://api.github.com/repos/changfei258-hub/RepoGuardian/installation", headers=headers, timeout=15, verify=False)
inst_id = r.json()["id"]
r2 = requests.post(f"https://api.github.com/app/installations/{inst_id}/access_tokens", headers=headers, timeout=15, verify=False)
tok = r2.json()["token"]
print("1️⃣ Token OK")

# AI analyze
result = analyze_issue("Issue #3", "Details")
print(f"2️⃣ AI: {result.get('category')}")

# Reply to Issue #3
h2 = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json", "User-Agent": "RepoGuardian"}
r3 = requests.post("https://api.github.com/repos/changfei258-hub/RepoGuardian/issues/3/comments",
    headers=h2, json={"body": result.get("answer", "Reviewed.")}, timeout=15, verify=False)
print(f"3️⃣ 回复状态: {r3.status_code}", "✅ 已回复!" if r3.ok else f"❌ {r3.text[:200]}")
