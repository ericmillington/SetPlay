#!/usr/bin/env python3
"""Real Google results, localized, via the DataForSEO SERP API.

Usage:
  python3 tools/serp.py --location "Clifton Park,New York,United States" \\
      --name "Eric Millington" --owned pixelheap.design,linkedin.com/in/eric-millington \\
      "Eric Millington" "pixelheap" "web designer Clifton Park NY"

Prints JSON: {"queries": [...], "search_snapshot": [...]} where search_snapshot entries
drop straight into audit.json. Each query also reports the local pack, knowledge panel
and People Also Ask presence.

Credentials: in a SetPlay cloud session the network proxy injects the DataForSEO login,
so nothing is needed here. Elsewhere set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD.
"""
import argparse
import base64
import json
import os
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(__file__))
from common import request  # noqa: E402

ENDPOINT = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"


def auth_header():
    login = os.environ.get("DATAFORSEO_LOGIN", "setplay")  # placeholder; proxy substitutes the real one
    pw = os.environ.get("DATAFORSEO_PASSWORD", "proxy")
    return "Basic " + base64.b64encode(f"{login}:{pw}".encode()).decode()


def classify(url, title, snippet, owned, name):
    host = urlparse(url).netloc.lower().removeprefix("www.")
    full = (url or "").lower()
    if any(o and (host == o or host.endswith("." + o) or o in full) for o in owned):
        return True, "you"
    text = f"{title} {snippet}".lower()
    if name:
        n = name.lower()
        if n in text:
            return False, "you"  # mentions the client; review: may still be a namesake
        surname = n.split()[-1]
        if surname in text:
            return False, "namesake"
    return False, "unrelated"  # review by hand: may be a competitor


def search(query, location, device, depth, language="en"):
    task = [{"keyword": query, "location_name": location, "language_code": language,
             "device": device, "os": "ios" if device == "mobile" else "windows", "depth": depth}]
    status, _, body = request(ENDPOINT, method="POST", data=task, headers={"Authorization": auth_header()}, timeout=90)
    try:
        payload = json.loads(body)
    except Exception:
        return {"error": f"HTTP {status}: {body[:300]!r}"}
    if status != 200 or payload.get("status_code") != 20000:
        return {"error": f"HTTP {status}: {payload.get('status_message')}"}
    t = payload["tasks"][0]
    if t.get("status_code") != 20000:
        return {"error": t.get("status_message")}
    return t["result"][0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--location", required=True, help='DataForSEO location name, e.g. "Clifton Park,New York,United States"')
    ap.add_argument("--device", default="mobile", choices=["mobile", "desktop"])
    ap.add_argument("--owned", default="", help="comma-separated domains / profile URLs the client controls")
    ap.add_argument("--name", default="", help="client's full name, for namesake detection")
    ap.add_argument("--depth", type=int, default=10)
    a = ap.parse_args()
    owned = [o.strip().lower().removeprefix("https://").removeprefix("http://").removeprefix("www.").rstrip("/")
             for o in a.owned.split(",") if o.strip()]

    out = {"location": a.location, "device": a.device, "queries": [], "search_snapshot": []}
    for q in a.queries:
        res = search(q, a.location, a.device, a.depth)
        if "error" in res:
            out["queries"].append({"query": q, "error": res["error"]})
            continue
        items = res.get("items") or []
        types = sorted({i.get("type") for i in items})
        label = f"{q}  (Google, {a.device}, {a.location.split(',')[0]})"
        summary = {"query": q, "result_types": types, "check_url": res.get("check_url"),
                   "local_pack": [], "knowledge_graph": None, "owned_ranks": []}
        rank = 0
        for i in items:
            kind = i.get("type")
            if kind == "organic":
                rank += 1
                if rank > a.depth:
                    continue
                url, title, snip = i.get("url", ""), i.get("title", ""), i.get("description") or ""
                is_owned, about = classify(url, title, snip, owned, a.name)
                if is_owned:
                    summary["owned_ranks"].append(rank)
                out["search_snapshot"].append({"query": label, "rank": rank, "title": title, "url": url,
                                               "owned": is_owned, "about": about,
                                               "sitelinks": len(i.get("links") or [])})
            elif kind == "local_pack":
                summary["local_pack"].append({"title": i.get("title"), "domain": i.get("domain"),
                                              "rating": (i.get("rating") or {}).get("value")})
            elif kind == "knowledge_graph":
                summary["knowledge_graph"] = {"title": i.get("title"), "subtitle": i.get("sub_title")}
        out["queries"].append(summary)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
