#!/usr/bin/env python3
"""Google PageSpeed Insights (Lighthouse + real-user Core Web Vitals) for the Website pillar.

Usage:  python3 tools/pagespeed.py https://www.example.com [mobile|desktop]

Tries the PageSpeed API first (adds real-user field data when Google has it). Set
PAGESPEED_API_KEY for a reliable quota. If the API fails, falls back to running Lighthouse
locally with the pre-installed Chromium (lab scores only, no field data).
"""
import json
import os
import subprocess
import sys
import tempfile
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(__file__))
from common import get_json  # noqa: E402


def run(url, strategy="mobile"):
    api = ("https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=" + quote(url, safe="")
           + f"&strategy={strategy}" + "".join(f"&category={c}" for c in ("performance", "accessibility", "best-practices", "seo")))
    if os.environ.get("PAGESPEED_API_KEY"):
        api += "&key=" + os.environ["PAGESPEED_API_KEY"]
    status, d = get_json(api, timeout=120)
    if status != 200:
        local = run_local(url, strategy)
        if local:
            local["note"] = f"PageSpeed API unavailable (HTTP {status}); local Lighthouse lab run, no field data."
            return local
        return {"error": f"HTTP {status}: {(d.get('error') or {}).get('message', d)}"}
    return summarize(url, strategy, d.get("lighthouseResult", {}), d.get("loadingExperience", {}), "pagespeed-api")


def run_local(url, strategy):
    chrome = os.environ.get("CHROME_PATH", "/opt/pw-browsers/chromium")
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "lh.json")
        cmd = ["npx", "-y", "lighthouse@12.8.2", url, "--quiet", "--output=json", f"--output-path={out}",
               "--chrome-flags=--headless=new --no-sandbox",
               "--only-categories=performance,accessibility,best-practices,seo"]
        cmd += ["--form-factor=mobile"] if strategy == "mobile" else ["--preset=desktop"]
        try:
            subprocess.run(cmd, env={**os.environ, "CHROME_PATH": chrome}, cwd=tmp, timeout=240,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return summarize(url, strategy, json.load(open(out)), {}, "local-lighthouse")
        except Exception:
            return None


def summarize(url, strategy, lh, experience, source):
    cats = {k: round((v.get("score") or 0) * 100) for k, v in lh.get("categories", {}).items()}
    audits = lh.get("audits", {})
    lab = {k: audits.get(k, {}).get("displayValue") for k in
           ("first-contentful-paint", "largest-contentful-paint", "total-blocking-time", "cumulative-layout-shift", "speed-index")}
    weight = audits.get("total-byte-weight", {}).get("numericValue")
    field = experience.get("metrics", {})
    cwv = {k: {"p75": v.get("percentile"), "rating": v.get("category")} for k, v in field.items()}
    a11y_fails = [r["id"] for r in lh.get("categories", {}).get("accessibility", {}).get("auditRefs", [])
                  if (audits.get(r["id"], {}).get("score") == 0)]
    return {"url": url, "strategy": strategy, "source": source, "scores": cats, "lab": lab,
            "page_weight_kb": round(weight / 1024) if weight else None,
            "field_core_web_vitals": cwv or "not enough real-user data",
            "field_overall": experience.get("overall_category"),
            "accessibility_failures": [{"id": i, "title": audits[i].get("title")} for i in a11y_fails]}


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    print(json.dumps(run(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else "mobile"), indent=2, ensure_ascii=False))
