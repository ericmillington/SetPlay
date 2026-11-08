#!/usr/bin/env python3
"""Render a client-ready Presence Report from audit.json.

Usage:  python3 tools/render_report.py clients/<slug>/audit.json [out.html]

Writes report.html next to audit.json by default. Output is one self-contained
HTML file that works in light/dark mode and prints cleanly to PDF (Cmd/Ctrl+P).
"""
import json
import sys
from html import escape
from pathlib import Path

LABELS = [(85, "Thriving", "Polish and protect what you've built."),
          (70, "Solid", "A few smart moves away from great."),
          (50, "Developing", "Real foundations, with real gaps to close."),
          (30, "Scattered", "Right now the internet is telling your story for you."),
          (0, "Unclaimed", "A blank slate, which is a great place to start.")]
SEV_ORDER = ["critical", "high", "medium", "low"]
STATUS_LABEL = {"active": "Active", "dormant": "Dormant", "unclaimed": "Unclaimed", "impersonation": "Impersonation",
                "outdated": "Outdated", "exposed": "Exposed", "unknown": "Unknown"}
ACTION_LABEL = {"keep": "Keep", "update": "Update", "consolidate": "Consolidate", "archive": "Archive",
                "delete": "Delete", "claim": "Claim", "report": "Report", "opt-out": "Opt out", "monitor": "Monitor"}


KIND_LABEL = {"own": "Yours", "you": "About you", "ns": "Namesake", "other": "Unrelated"}


def kind(r):
    """Classify a search result: own (client controls it), you (about them), ns (namesake), other (unrelated/competitor)."""
    if r.get("owned"):
        return "own"
    return {"namesake": "ns", "unrelated": "other", "competitor": "other"}.get(r.get("about"), "you")


def e(x):
    return escape(str(x)) if x is not None else ""


def presence_score(pillars):
    scored = [p for p in pillars if p.get("score") is not None]
    total_w = sum(p["weight"] for p in scored)
    if not total_w:
        return None
    return round(sum(p["score"] / 5 * p["weight"] for p in scored) / total_w * 100)


def label_for(score):
    for floor, name, line in LABELS:
        if score >= floor:
            return name, line
    return LABELS[-1][1:]


def ring(score):
    r, c = 70, 2 * 3.14159 * 70
    off = c * (1 - score / 100)
    return f'''<svg class="ring" viewBox="0 0 180 180" role="img" aria-label="Presence Score {score} out of 100">
  <circle cx="90" cy="90" r="{r}" class="ring-track"/>
  <circle cx="90" cy="90" r="{r}" class="ring-fill" stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}" transform="rotate(-90 90 90)"/>
  <text x="90" y="88" class="ring-num">{score}</text><text x="90" y="114" class="ring-of">of 100</text></svg>'''


def section(title, eyebrow, body, sid=""):
    return f'<section {f"id={sid!r}" if sid else ""}><p class="eyebrow">{e(eyebrow)}</p><h2>{e(title)}</h2>{body}</section>'


def render(audit):
    c = audit["client"]
    pillars = audit["pillars"]
    score = presence_score(pillars)
    if score is None:
        sys.exit("No pillar scores yet; fill in audit.json first.")
    label, line = label_for(score)

    # Pillars
    prow = []
    for p in pillars:
        s = p.get("score")
        pct = 0 if s is None else s / 5 * 100
        prow.append(f'''<div class="pillar"><div class="pillar-head"><span>{e(p["name"])}</span>
          <span class="pillar-score">{"–" if s is None else s}<small>/5</small></span></div>
          <div class="bar"><span style="width:{pct:.0f}%" class="lvl-{int(s or 0)}"></span></div>
          <p class="muted">{e(p.get("notes", ""))}</p></div>''')
    pillars_html = f'<div class="pillars">{"".join(prow)}</div>'

    # Search snapshot
    snap = audit.get("search_snapshot", [])
    snap_html = ""
    if snap:
        queries = {}
        for r in snap:
            queries.setdefault(r["query"], []).append(r)
        blocks = []
        for q, rows in queries.items():
            rows = sorted(rows, key=lambda r: r.get("rank", 99))
            owned = sum(1 for r in rows if r.get("owned"))
            dots = "".join(f'<span class="dot {kind(r)}" title="#{r.get("rank")}: {e(r.get("title"))}"></span>' for r in rows)
            items = "".join(f'''<li><span class="rank">{e(r.get("rank"))}</span><div><strong>{e(r.get("title"))}</strong>
                <span class="url">{e(r.get("url"))}</span></div>
                <span class="tag t-{kind(r)}">{KIND_LABEL[kind(r)]}</span></li>''' for r in rows)
            blocks.append(f'''<div class="query"><div class="query-head"><code>{e(q)}</code>
              <span class="dots">{dots}</span><span class="muted">You control {owned} of {len(rows)}</span></div>
              <ol class="results">{items}</ol></div>''')
        snap_html = section("What people see when they search for you", "Search snapshot", "".join(blocks), "search")

    # Inventory
    inv = audit.get("inventory", [])
    inv_html = ""
    if inv:
        rows = "".join(f'''<tr><td><strong>{e(i.get("platform"))}</strong><span class="url">{e(i.get("handle") or i.get("url") or "")}</span></td>
            <td><span class="chip s-{e(i.get("status", "unknown"))}">{e(STATUS_LABEL.get(i.get("status"), i.get("status")))}</span></td>
            <td class="center">{"✓" if i.get("consistent") else ("✗" if i.get("consistent") is False else "–")}</td>
            <td><span class="chip a-{e(i.get("action", "keep"))}">{e(ACTION_LABEL.get(i.get("action"), i.get("action")))}</span></td>
            <td class="muted">{e(i.get("notes", ""))}</td></tr>''' for i in inv)
        counts = {}
        for i in inv:
            counts[i.get("action")] = counts.get(i.get("action"), 0) + 1
        summary = " · ".join(f"{n} to {ACTION_LABEL.get(a, a).lower()}" for a, n in sorted(counts.items(), key=lambda x: -x[1]))
        inv_html = section("Your footprint, account by account", f"Inventory: {len(inv)} items",
                           f'<p class="lede">{e(summary)}</p><div class="table-wrap"><table><thead><tr><th>Where</th><th>Status</th><th>On-brand</th><th>Action</th><th>Notes</th></tr></thead><tbody>{rows}</tbody></table></div>',
                           "inventory")

    # Findings
    fnd = sorted(audit.get("findings", []), key=lambda f: SEV_ORDER.index(f.get("severity", "low")))
    pname = {p["id"]: p["name"] for p in pillars}
    fnd_html = ""
    if fnd:
        cards = "".join(f'''<article class="finding sev-{e(f.get("severity"))}"><div class="finding-meta">
            <span class="sev">{e(f.get("severity", "").title())}</span><span class="muted">{e(pname.get(f.get("pillar"), f.get("pillar")))}</span></div>
            <h3>{e(f.get("title"))}</h3><p>{e(f.get("detail"))}</p>
            {f'<p class="evidence">Evidence: {e(f["evidence"])}</p>' if f.get("evidence") else ""}</article>''' for f in fnd)
        tally = " · ".join(f'{sum(1 for f in fnd if f.get("severity") == s)} {s}' for s in SEV_ORDER if any(f.get("severity") == s for f in fnd))
        fnd_html = section("What we found", f"Findings: {tally}", f'<div class="findings">{cards}</div>', "findings")

    # Roadmap
    rm = audit.get("roadmap", {})
    cols = []
    for key, title, sub in [("now", "Now", "This week: the urgent and the easy"), ("next", "Next", "This month: the foundations"), ("later", "Later", "This quarter: growth")]:
        items = "".join(f'''<li><div class="rm-top"><strong>{e(r.get("title"))}</strong><span class="effort" title="Effort">{e(r.get("effort", ""))}</span></div>
            <p>{e(r.get("detail", ""))}</p><span class="owner">{e({"client": "You", "marketer": "We handle it", "both": "Together"}.get(r.get("owner"), r.get("owner", "")))}</span></li>''' for r in rm.get(key, []))
        cols.append(f'<div class="rm-col"><h3>{title}</h3><p class="muted">{sub}</p><ol>{items}</ol></div>')
    rm_html = section("Your roadmap", "The plan", f'<div class="roadmap">{"".join(cols)}</div><p class="muted small">Effort: S = under an hour · M = a few hours · L = a project</p>', "roadmap")

    nav = "".join(f'<a href="#{i}">{t}</a>' for i, t, ok in [("score", "Score", True), ("search", "Search", snap), ("inventory", "Inventory", inv), ("findings", "Findings", fnd), ("roadmap", "Roadmap", True)] if ok)

    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Presence Report · {e(c["name"])}</title>
<meta name="robots" content="noindex,nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head>
<body>
<header class="top"><div class="wrap top-inner"><span class="brand">SetPlay</span><nav>{nav}</nav></div></header>
<main class="wrap">
<section class="hero" id="score">
  <div><p class="eyebrow">Presence Report · {e(c.get("date"))}</p>
  <h1>{e(c["name"])}</h1>
  {f'<p class="tagline">{e(c["tagline"])}</p>' if c.get("tagline") else ""}
  <p class="label">{e(label)}</p><p class="lede">{e(line)}</p>
  <p class="summary">{e(audit.get("summary", ""))}</p></div>
  {ring(score)}
</section>
{section("Six pillars of a responsible presence", "Breakdown", pillars_html)}
{snap_html}{inv_html}{fnd_html}{rm_html}
</main>
<footer class="wrap"><p>Prepared by {e(c.get("prepared_by", "SetPlay"))} for {e(c["name"])} on {e(c.get("date"))}. Based on publicly available information at that date; search results vary by location and over time. Confidential.</p></footer>
</body></html>'''


CSS = """
:root{--bg:#faf7f2;--panel:#fff;--ink:#1d1b18;--muted:#6b655c;--line:#e7e1d6;--accent:#2f5d50;--accent-soft:#dcebe5;
--crit:#a3242b;--high:#c2571a;--med:#b38a12;--low:#5b6f8a;--own:#2f5d50;--ns:#c9bfae;--other:#8a7f6e;
--serif:'Fraunces',Georgia,serif;--sans:'Inter',system-ui,-apple-system,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#151412;--panel:#1e1c19;--ink:#efe9df;--muted:#a59d90;--line:#34302a;
--accent:#7fbfa9;--accent-soft:#22332d;--crit:#ef7a7f;--high:#f0a06a;--med:#e3c25a;--low:#93a8c6;--own:#7fbfa9;--ns:#4b453c;--other:#8a7f6e}}
:root[data-theme=dark]{--bg:#151412;--panel:#1e1c19;--ink:#efe9df;--muted:#a59d90;--line:#34302a;--accent:#7fbfa9;--accent-soft:#22332d;
--crit:#ef7a7f;--high:#f0a06a;--med:#e3c25a;--low:#93a8c6;--own:#7fbfa9;--ns:#4b453c}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 var(--sans);-webkit-font-smoothing:antialiased}
.wrap{max-width:1040px;margin:0 auto;padding:0 16px}
.top{position:sticky;top:0;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);z-index:5}
.top-inner{display:flex;justify-content:space-between;align-items:center;height:56px;gap:16px}
.brand{font:600 20px var(--serif);letter-spacing:-.01em}
nav{display:flex;gap:18px;overflow-x:auto}nav a{color:var(--muted);text-decoration:none;font-size:14px;white-space:nowrap}nav a:hover{color:var(--ink)}
h1,h2,h3{font-family:var(--serif);font-weight:600;letter-spacing:-.015em;line-height:1.15;margin:0}
h1{font-size:clamp(40px,7vw,64px)}h2{font-size:clamp(26px,4vw,34px);margin-bottom:24px}h3{font-size:19px}
.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:12px;font-weight:600;color:var(--accent);margin:0 0 10px}
.muted{color:var(--muted)}.small{font-size:13px}.center{text-align:center}
section{padding:56px 0;border-bottom:1px solid var(--line)}
.hero{display:grid;grid-template-columns:1fr 220px;gap:40px;align-items:center;padding-top:64px}
.tagline{color:var(--muted);font-size:18px;margin:8px 0 0}
.label{font:600 28px var(--serif);color:var(--accent);margin:28px 0 0}.lede{font-size:18px;margin:4px 0 0}
.summary{max-width:60ch;margin-top:20px;color:var(--muted)}
.ring{width:100%;max-width:220px}.ring-track{fill:none;stroke:var(--line);stroke-width:14}
.ring-fill{fill:none;stroke:var(--accent);stroke-width:14;stroke-linecap:round}
.ring-num{font:600 52px var(--serif);fill:var(--ink);text-anchor:middle}.ring-of{font:500 13px var(--sans);fill:var(--muted);text-anchor:middle}
.pillars{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:16px}
.pillar{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px}
.pillar-head{display:flex;justify-content:space-between;align-items:baseline;font-weight:600}
.pillar-score{font:600 24px var(--serif)}.pillar-score small{font-size:13px;color:var(--muted)}
.pillar p{margin:12px 0 0;font-size:14px}
.bar{height:8px;background:var(--line);border-radius:99px;margin-top:10px;overflow:hidden}
.bar span{display:block;height:100%;border-radius:99px;background:var(--accent)}
.bar .lvl-0,.bar .lvl-1{background:var(--crit)}.bar .lvl-2{background:var(--high)}.bar .lvl-3{background:var(--med)}
.query{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px;margin-bottom:16px}
.query-head{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center;margin-bottom:12px}
.query-head code{font-size:15px;background:var(--accent-soft);padding:4px 10px;border-radius:8px}
.dots{display:flex;gap:5px}.dot{width:14px;height:14px;border-radius:4px;background:var(--other);opacity:.5}
.dot.own{background:var(--own);opacity:1}.dot.you{background:var(--med);opacity:1}.dot.ns{background:var(--ns);opacity:1}
.results{list-style:none;padding:0;margin:0}
.results li{display:grid;grid-template-columns:28px 1fr auto;gap:12px;align-items:start;padding:10px 0;border-top:1px solid var(--line)}
.rank{font:600 15px var(--serif);color:var(--muted)}
.url{display:block;font-size:13px;color:var(--muted);word-break:break-all}
.tag{font-size:12px;font-weight:600;padding:3px 9px;border-radius:99px;white-space:nowrap}
.t-own{background:var(--accent-soft);color:var(--accent)}.t-you{background:color-mix(in srgb,var(--med) 18%,transparent);color:var(--med)}.t-ns{background:var(--line);color:var(--muted)}.t-other{border:1px solid var(--line);color:var(--muted)}
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:var(--panel)}
table{width:100%;border-collapse:collapse;font-size:14px;min-width:680px}
th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);padding:12px 16px;border-bottom:1px solid var(--line)}
td{padding:12px 16px;border-bottom:1px solid var(--line);vertical-align:top}tr:last-child td{border-bottom:0}
.chip{display:inline-block;font-size:12px;font-weight:600;padding:3px 9px;border-radius:99px;background:var(--line);white-space:nowrap}
.s-active{background:var(--accent-soft);color:var(--accent)}.s-impersonation,.s-exposed{background:color-mix(in srgb,var(--crit) 15%,transparent);color:var(--crit)}
.s-dormant,.s-outdated{background:color-mix(in srgb,var(--med) 18%,transparent);color:var(--med)}
.a-keep{background:transparent;border:1px solid var(--line)}.a-delete,.a-report,.a-opt-out{color:var(--crit)}.a-claim,.a-update{color:var(--accent)}
.findings{display:grid;gap:14px}
.finding{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--low);border-radius:12px;padding:18px 20px}
.finding p{margin:8px 0 0}.finding-meta{display:flex;gap:12px;font-size:13px;margin-bottom:6px}
.sev{font-weight:700;text-transform:uppercase;letter-spacing:.08em;font-size:11px}
.sev-critical{border-left-color:var(--crit)}.sev-critical .sev{color:var(--crit)}
.sev-high{border-left-color:var(--high)}.sev-high .sev{color:var(--high)}
.sev-medium{border-left-color:var(--med)}.sev-medium .sev{color:var(--med)}.sev-low .sev{color:var(--low)}
.evidence{font-size:13px;color:var(--muted);word-break:break-all}
.roadmap{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.rm-col{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px}
.rm-col h3{font-size:24px}.rm-col>p{margin:4px 0 12px;font-size:14px}
.rm-col ol{list-style:none;padding:0;margin:0;counter-reset:r}
.rm-col li{padding:14px 0;border-top:1px solid var(--line)}.rm-col li p{margin:6px 0;font-size:14px;color:var(--muted)}
.rm-top{display:flex;justify-content:space-between;gap:10px}
.effort{font:600 12px var(--sans);border:1px solid var(--line);border-radius:6px;padding:1px 7px;height:fit-content}
.owner{font-size:12px;font-weight:600;color:var(--accent)}
footer{padding:40px 16px 64px;font-size:13px;color:var(--muted)}
@media (max-width:760px){.hero{grid-template-columns:1fr}.ring{max-width:170px}.roadmap{grid-template-columns:1fr}}
@media print{.top{display:none}section{break-inside:avoid-page;padding:32px 0}body{background:#fff}
.pillar,.query,.finding,.rm-col{break-inside:avoid}}
"""

if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) == 3 else src.with_name("report.html")
    audit = json.loads(src.read_text())
    out.write_text(render(audit))
    print(f"Wrote {out}  (Presence Score: {presence_score(audit['pillars'])})")
