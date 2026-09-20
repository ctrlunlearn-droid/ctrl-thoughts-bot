"""Instagram long-lived token ko refresh karta hai (60 din ki validity dobara shuru).

Local: IG_ACCESS_TOKEN set karke `python refresh_token.py`
Actions: `--quiet` sirf naya token print karta hai.
Rule: token kam se kam 24 ghante purana ho aur expire na hua ho.
"""
import os
import sys

import requests

token = os.environ["IG_ACCESS_TOKEN"]
r = requests.get(
    "https://graph.instagram.com/refresh_access_token",
    params={"grant_type": "ig_refresh_token", "access_token": token},
    timeout=30,
)
data = r.json()
if r.status_code >= 400 or "access_token" not in data:
    sys.exit(f"Refresh fail: {data}")
if "--quiet" in sys.argv:
    print(data["access_token"])
else:
    print(f"Naya token (expires in {data.get('expires_in')} sec):\n{data['access_token']}")
