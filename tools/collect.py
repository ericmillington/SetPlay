#!/usr/bin/env python3
"""Run every automated audit collector for a client in one go.

Usage:  python3 tools/collect.py <slug>

Reads clients/<slug>/audit.json → client.inputs:
  {
    "name": "Eric Millington",            # person's public name
    "business": "Pixelheap",              # optional
    "profession": "web designer",         # what clients search for
    "location": "Clifton Park,New York,United States",   # DataForSEO location name
    "town": "Clifton Park NY",            # for query text
    "site": "https://www.pixelheap.design",
    "owned": ["pixelheap.design", "linkedin.com/in/eric-millington"],
    "handles": ["pixelheap", "ericmillington"],
    "queries": []                         # optional extra queries
  }

Writes clients/<slug>/collected/{site-check,pagespeed,domain,handles,serp}.json and prints a
one-line status per collector. It collects only; scoring and findings are written afterwards.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"


def run(name, args, out, timeout=300):
    try:
        p = subprocess.run([sys.executable, str(TOOLS / name), *args], capture_output=True, text=True, timeout=timeout)
        data = json.loads(p.stdout)
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    except Exception as e:
        out.write_text(json.dumps({"error": str(e)}))
        return {"error": str(e)}


def default_queries(i):
    q = []
    if i.get("name"):
        q.append(f'"{i["name"]}"')
        if i.get("profession"):
            q.append(f'{i["name"]} {i["profession"]}')
    if i.get("business"):
        q.append(i["business"])
    if i.get("profession") and i.get("town"):
        q.append(f'{i["profession"]} {i["town"]}')
    if i.get("site"):
        q.append(urlparse(i["site"]).netloc.removeprefix("www."))
    return q + i.get("queries", [])


def main(slug):
    cdir = ROOT / "clients" / slug
    audit = json.loads((cdir / "audit.json").read_text())
    i = audit["client"].get("inputs")
    if not i:
        sys.exit(f"Add client.inputs to {cdir/'audit.json'} first (see this script's docstring).")
    out = cdir / "collected"
    out.mkdir(exist_ok=True)
    status = {}

    if i.get("site"):
        d = run("site_check.py", [i["site"]], out / "site-check.json")
        status["site-check"] = d.get("error") or f'{len(d.get("issues", []))} issues'
        d = run("pagespeed.py", [i["site"], "mobile"], out / "pagespeed.json")
        status["pagespeed"] = d.get("error") or f'{d.get("scores")} ({d.get("source")})'
        dom = urlparse(i["site"]).netloc
        d = run("domain_check.py", [dom], out / "domain.json")
        status["domain"] = d.get("error") or f'{d["rdap"].get("registrar")}, {d.get("days_to_expiry")} days to expiry, {len(d["issues"])} issues'

    if i.get("handles"):
        d = run("handles.py", i["handles"], out / "handles.json")
        status["handles"] = ", ".join(f'{r["platform"]}:{r["state"]}' for r in d if r["state"] in ("taken", "available")) if isinstance(d, list) else d.get("error")

    if i.get("location"):
        args = ["--location", i["location"], "--owned", ",".join(i.get("owned", [])), "--name", i.get("name", ""), *default_queries(i)]
        d = run("serp.py", args, out / "serp.json", timeout=600)
        errs = [q["error"] for q in d.get("queries", []) if q.get("error")] if "queries" in d else [d.get("error")]
        status["serp"] = (f"ERROR: {errs[0]}" if errs else
                          "; ".join(f'{q["query"]} → owned ranks {q["owned_ranks"] or "none"}' for q in d["queries"]))

    for k, v in status.items():
        print(f"{k:11} {v}")
    print(f"\nRaw data in {out}. Next: score pillars and write findings in audit.json.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
