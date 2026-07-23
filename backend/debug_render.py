"""Debug endpoint for Render."""
import sys, os, jwt, time, requests, urllib3
urllib3.disable_warnings()
sys.path.insert(0, ".")

from app.config import settings

# Check env vars
print("APP_ID:", repr(settings.GITHUB_APP_ID))
print("KEY from env exists:", bool(os.getenv("GITHUB_PRIVATE_KEY")))
print("KEY length:", len(settings.github_private_key))
print("KEY starts with:", settings.github_private_key[:50])

# Try JWT
try:
    payload = {"iat": int(time.time())-60, "exp": int(time.time())+600, "iss": "4372444"}
    token = jwt.encode(payload, settings.github_private_key, algorithm="RS256")
    print("JWT: OK, length:", len(token))
except Exception as e:
    print("JWT FAIL:", str(e))
