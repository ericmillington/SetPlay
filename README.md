# SetPlay

**Know what's out there. Own what's yours. Build something worth finding.**

SetPlay is a done-for-you digital presence service. We take a full inventory of
a client's digital footprint, score it, deliver a clear plan, and then build a
responsible, beautiful website that anchors their presence.

## How the work flows

```
 Intake  ─▶  Footprint audit  ─▶  Report + roadmap  ─▶  Cleanup  ─▶  Website  ─▶  Care plan
 (client)    (/footprint-audit)   (tools/render_report)  (client+us)  (/presence-site)
```

| Stage | What happens | Where it lives |
|---|---|---|
| 1. Intake | Client fills in the questionnaire and signs the consent form | `templates/intake.md` |
| 2. Audit | Search, profile inventory, privacy exposure, website check | `framework/audit-checklist.md`, `/footprint-audit` |
| 3. Report | Scored across 6 pillars, findings, a Now / Next / Later roadmap | `tools/render_report.py` |
| 4. Website | Brief, then a fast, accessible, privacy-respecting site | `templates/site-brief.md`, `/presence-site` |

## Repo layout

```
docs/offer.md                 The product: positioning, packages, pricing, process
docs/principles.md            What "responsible web presence" means (our promise)
framework/audit-checklist.md  Everything we check, pillar by pillar
framework/scoring.md          The 0–100 Presence Score rubric
templates/                    Intake, consent, site brief
tools/new_client.sh           Scaffold a client folder
tools/site_check.py           Automated check of an existing website (stdlib only)
tools/render_report.py        audit.json → a polished, client-ready HTML report
clients/pixelheap/            Pilot audit (Pixelheap / Eric Millington), the reference example
.claude/skills/               Claude workflows: /footprint-audit, /presence-site
```

## Quick start

```bash
tools/new_client.sh "Jane Doe"                         # creates clients/jane-doe/
python3 tools/site_check.py https://janedoe.com > clients/jane-doe/site-check.json
python3 tools/render_report.py clients/jane-doe/audit.json   # writes report.html next to it
```

Or ask Claude to do it: `/footprint-audit jane-doe`.

Open `clients/pixelheap/report.html` to see a finished deliverable.

> **Client data is private.** Everything under `clients/` except the pilot is
> git-ignored on purpose. Store real client folders somewhere access-controlled.
