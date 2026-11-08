---
name: footprint-audit
description: Run a SetPlay digital footprint audit for a client folder (clients/<slug>/) — search snapshot, profile inventory, privacy exposure, automated website check — then score it and render the client report. Use when the user says "audit <client/domain>" or /footprint-audit.
---

# Footprint audit

Argument: a client slug, name, or domain. If `clients/<slug>/` doesn't exist, run
`tools/new_client.sh "<Name>"` first.

Follow `framework/audit-checklist.md`, and score with `framework/scoring.md`. The finished
example is `clients/pixelheap/`. Match its depth and tone.

## Steps

1. **Consent and intake.** Read `clients/<slug>/intake.md`. If consent isn't signed and the
   client isn't the user themself, stop and say so.
2. **Website check.** Run `SSL_CERT_FILE=/root/.ccr/ca-bundle.crt python3 tools/site_check.py <url> > clients/<slug>/site-check.json`.
   - If it reports `Tunnel connection failed: 403`, the cloud environment's network policy is blocking
     the host. Ask to allow that exact host (and its `www.` variant) with the environment
     tools. Don't work around the block.
   - Save the home page and the key inner pages to `evidence/` with curl, and extract the text, links,
     scripts and `meta generator`. Read the copy itself: inconsistent positioning, mixed voice,
     conflicting numbers and stale dates are often the most valuable findings.
   - `http_redirects_to_https: null` means the check couldn't connect, not that it failed. Verify by hand.
3. **Search snapshot.** Run WebSearch, in parallel, for: the person's name in quotes, name + profession,
   name + town, business + service + town, and the bare domain. Record the top 5 per query in
   `search_snapshot`, with `owned` and `about` ∈ `you | namesake | competitor | unrelated`.
   Note in the finding that the snapshot came from one engine, and recommend a signed-out
   Google check from the client's area.
4. **Inventory.** List every profile linked from the site, every one found in search, and the
   obvious gaps (Google Business Profile, Behance/Dribbble for creatives, chamber/directories for local).
   Statuses: `active | dormant | unclaimed | impersonation | outdated | exposed | unknown`.
   Actions: `keep | update | consolidate | archive | delete | claim | report | opt-out | monitor`.
5. **Privacy.** Use public sources only. Never buy broker reports, guess passwords or log in. Record a
   personal phone or address exposure on the client's own properties. Leave the broker sweep
   and breach check as roadmap items unless the client has provided emails and asked for them.
6. **Score and write.** Fill `pillars` (score each 0–5 against the anchors, with notes that cite numbers),
   `findings` (severity, plain-English detail with a concrete fix, evidence), and `roadmap`
   (now/next/later, effort S/M/L, owner client/marketer/both). Write the `summary` warmly: open with what's
   strong, then name the single biggest problem.
7. **Render.** Run `python3 tools/render_report.py clients/<slug>/audit.json`, screenshot it at 1280 and 390
   wide with Playwright to check it, then send `report.html` to the user.

Be honest. Don't inflate scores to be kind, and don't claim anything that isn't in the evidence.
