#!/usr/bin/env python3
"""Read-only inventory of the original OBSIDIAN Actions cache.

Research only. Does not restore a cache, modify workflows, contact SMG, or
read private account data. Requires GH_TOKEN with actions:read for this repo.
Usage: python backtest/obsidian_walk_forward/inventory_original_cache.py
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO = "Dirtyhandgernades/Dudebot"
KEY = "intraday-bars-v1-37386241124"
URL = "https://api.github.com/repos/" + REPO + "/actions/caches?" + urllib.parse.urlencode({"key": KEY, "per_page": 100})

def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print(json.dumps({"status": "NOT_CHECKED_NO_READ_TOKEN", "key": KEY}))
        return 2
    request = urllib.request.Request(URL, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "obsidian-research-cache-inventory",
    })
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        print(json.dumps({"status": "HTTP_ERROR", "code": exc.code, "key": KEY}))
        return 3
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "REQUEST_ERROR", "error_type": type(exc).__name__, "key": KEY}))
        return 4
    caches = [c for c in payload.get("actions_caches", []) if c.get("key") == KEY]
    print(json.dumps({
        "status": "EXACT_CACHE_PRESENT" if caches else "EXACT_CACHE_NOT_LISTED",
        "key": KEY,
        "total_count": payload.get("total_count"),
        "matches": [{
            "id": c.get("id"), "key": c.get("key"), "ref": c.get("ref"),
            "size_in_bytes": c.get("size_in_bytes"),
            "created_at": c.get("created_at"), "last_accessed_at": c.get("last_accessed_at")
        } for c in caches],
        "note": "Cache metadata only. Presence is not byte recovery or verified signal reconstruction."
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    sys.exit(main())
