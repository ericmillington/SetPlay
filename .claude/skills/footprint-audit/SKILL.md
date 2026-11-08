---
name: footprint-audit
description: Run a SetPlay digital footprint audit for a client folder (clients/<slug>/) — automated collection (Google SERPs, site check, Lighthouse, domain/email security, handles), then judgment, scoring and the client report. Use when the user says "audit <client/domain>" or /footprint-audit.
---

# Footprint audit (runs end to end without the user)

Argument: a client slug, name, or domain. The reference example is `clients/pixelheap/`, so match
its depth and tone. The method is `framework/audit-checklist.md`, and scoring follows `framework/scoring.md`.

## 1. Set up

- If `clients/<slug>/` doesn't exist, run `tools/new_client.sh "<Name>"`.
- Consent: if the intake isn't signed and the client isn't the user, stop and say so.
- Fill `client.inputs` in `audit.json` (see the `tools/collect.py` docstring). If all you have is a domain, read
  the site first to find the name, profession, town and linked profiles. Guess handles from the
  domain and name.

## 2. Collect (automated)

```bash
python3 tools/collect.py <slug>      # writes clients/<slug>/collected/*.json
```

It runs `site_check.py`, `pagespeed.py` (PageSpeed API, falling back to local Lighthouse), `domain_check.py`
(RDAP, MX/SPF/DMARC), `handles.py`, and `serp.py` (real Google results, localized and mobile, via DataForSEO).

- **If serp reports 401**, the DataForSEO credential isn't saved on the environment. Run the same queries with
  WebSearch instead, label them `(WebSearch, provisional)`, and **never score Discoverability below 2 on WebSearch
  misses alone**, because it missed Pixelheap's Google #1. Mention once that adding the DataForSEO login makes this exact.
- If a host is blocked (`Tunnel connection failed: 403`), the network policy changed. Report it, and don't work around it.
- Handles marked `check by hand` (Instagram, X, TikTok…) are login-walled. Note them as unknown and don't guess.

## 3. Read like a human

Save the home page and the key inner pages to `evidence/` with curl, and read the copy. The most valuable
findings are often editorial: conflicting positioning, mixed I/we, contradictory numbers ("20+" vs "25+"),
stale blogs, personal phone numbers, and required fields that collect more than they need.

## 4. Judge, score, write

Fill in the following:

- `search_snapshot` from `collected/serp.json`. Re-label `about` by hand, since the script can't tell a competitor from an unrelated result.
- `inventory`
- `pillars`: 0–5 against the anchors, with notes that cite numbers
- `findings`: severity, plain-English detail with a concrete fix, and evidence pointing to the `collected/…` file
- `roadmap`: now/next/later, effort S/M/L, and owner

The summary opens with what's strong, then names the single biggest gap. Be honest: don't inflate scores, and don't
claim anything that isn't in the evidence.

## 5. Privacy limits

Use public sources only. Never buy broker reports, log in as the client, or guess passwords. Leave the broker sweep and breach
check as roadmap items unless the client has provided emails and asked for them.

## 6. Deliver

Run `python3 tools/render_report.py clients/<slug>/audit.json`, screenshot it at 1280 and 390 wide with Playwright, look at the
screenshots, then send `report.html`.
