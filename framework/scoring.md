# The Presence Score (0–100)

Each of the six pillars is scored 0–5 and then weighted. `render_report.py` does the math:

```
Presence Score = Σ (pillar_score / 5 × weight) / Σ weight × 100
```

| Pillar | Default weight | Why |
|---|---|---|
| Discoverability | 20 | Being found, by the right people, as yourself |
| Consistency | 15 | Trust comes from coherence |
| Ownership & Control | 20 | If you don't control it, you can lose it |
| Privacy & Safety | 20 | Responsible presence includes what you *don't* show |
| Reputation & Content | 10 | The story the results tell |
| Website Quality | 15 | Your home base |

For local businesses, consider moving 5 points from Privacy to Reputation, because reviews matter more.

## Pillar anchors

Use these anchors so that scores stay comparable between clients and between re-audits.

| Score | Discoverability | Consistency | Ownership & Control | Privacy & Safety | Reputation & Content | Website Quality |
|---|---|---|---|---|---|---|
| **0** | Nothing about them on page 1 | No profiles / contradictory | No domain, no access to key accounts | Home address + phone on many broker sites, multiple breaches | Prominent negative results, nothing positive | No site, or a broken one |
| **1** | Mostly namesakes; one owned result | Wildly different names/photos/bios | Domain held by an ex-vendor; lost logins | Address exposed, little hygiene | Mostly outdated or off-brand | Site exists but outdated, insecure, not mobile |
| **2** | 2–3 owned results, buried | Some match, many stale | Owns some assets, gaps (no 2FA, no own email) | Several broker listings, some exposure | Thin; few reviews or mentions | Works, but slow / poor SEO / trackers |
| **3** | Owns ~half of page 1 | Mostly consistent; a few stale | Owns domain + main accounts; some dormant clutter | A few listings; no address on own properties | Neutral-positive; some outdated | Solid basics, few issues |
| **4** | Owns most of page 1, top result is theirs | Consistent, a minor nit or two | Full control, 2FA, own email, handles reserved | Minimal exposure; opted out of major brokers | Positive, current, some proof | Fast, accessible, secure, clear CTA |
| **5** | Owns page 1; rich results / knowledge panel | Identical name, photo, bio, links everywhere | Everything owned, documented, recoverable | Clean; monitoring in place | Strong reviews/press, featured on site | Exemplary: meets every principle in `docs/principles.md` |

## Labels

| Score | Label | Tone in the report |
|---|---|---|
| 85–100 | **Thriving** | Polish and protect |
| 70–84 | **Solid** | A few smart moves away from great |
| 50–69 | **Developing** | Real foundations, real gaps |
| 30–49 | **Scattered** | The internet is telling your story for you |
| 0–29 | **Unclaimed** | A blank slate, which is a great place to start |

## Finding severity

- **critical**: active risk to safety, money, or identity (impersonation, exposed home address for an at-risk client, a domain about to expire, a breached password still in use)
- **high**: materially hurts trust or discoverability (namesake outranks them, the site is broken on mobile)
- **medium**: inconsistent or outdated details that weaken the impression
- **low**: polish

## Re-audits

Re-score at launch and quarterly on the Care Plan. Showing the score going up (e.g. 41 → 78)
is the strongest testimonial you'll get. Keep every `audit.json` with its date.
