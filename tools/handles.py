#!/usr/bin/env python3
"""Check whether a handle is taken on major platforms.

Usage:  python3 tools/handles.py pixelheap [ericmillington ...]

Only platforms that answer reliably to signed-out requests are checked automatically.
Instagram, X, TikTok, LinkedIn and Threads hide behind login walls and are listed as
"check by hand" with the URL to open.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import request, get_json  # noqa: E402

# name: (url template, how to read the response)
AUTO = {
    "GitHub": "https://github.com/{h}",
    "Bluesky": "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={h}.bsky.social",
    "Behance": "https://www.behance.net/{h}",
    "Dribbble": "https://dribbble.com/{h}",
    "YouTube": "https://www.youtube.com/@{h}",
    "Vimeo": "https://vimeo.com/{h}",
}
MANUAL = {
    "Instagram": "https://www.instagram.com/{h}/",
    "X": "https://x.com/{h}",
    "TikTok": "https://www.tiktok.com/@{h}",
    "Threads": "https://www.threads.net/@{h}",
    "LinkedIn (company)": "https://www.linkedin.com/company/{h}/",
    "Facebook": "https://www.facebook.com/{h}",
    "Pinterest": "https://www.pinterest.com/{h}/",  # returns 200 for every handle
    "Medium": "https://medium.com/@{h}",            # blocks signed-out checks
}


def check(platform, tmpl, h):
    url = tmpl.format(h=h)
    if platform == "Bluesky":
        status, d = get_json(url)
        state = "taken" if status == 200 else ("available" if status == 400 else "unknown")
        return {"platform": platform, "handle": h, "state": state, "url": f"https://bsky.app/profile/{h}.bsky.social", "http": status}
    status, headers, body = request(url, timeout=20)
    if status == 200:
        text = body[:200000].decode("utf-8", "replace").lower()
        # Some sites return 200 with a "not found" page
        if any(s in text for s in ("page not found", "this page isn't available", "couldn't find", "user not found")):
            state = "available"
        else:
            state = "taken"
    elif status == 404:
        state = "available"
    else:
        state = "unknown"  # blocked (403/429) or redirect to login
    return {"platform": platform, "handle": h, "state": state, "url": url, "http": status}


def main(handles):
    out = []
    for h in handles:
        h = h.lstrip("@")
        out += [check(p, t, h) for p, t in AUTO.items()]
        out += [{"platform": p, "handle": h, "state": "check by hand", "url": t.format(h=h)} for p, t in MANUAL.items()]
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
