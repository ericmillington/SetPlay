#!/usr/bin/env python3
"""Domain ownership and email-security check (Ownership & Privacy pillars).

Usage:  python3 tools/domain_check.py pixelheap.design

Reports registrar, created/expiry dates, days to expiry, registrant privacy hints (RDAP),
nameservers/host hints, and email records: MX, SPF, DMARC. A domain with no DMARC/SPF can be
used by anyone to send email "from" the client, which is a real impersonation risk.
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import get_json  # noqa: E402


def dns(name, rtype):
    status, d = get_json(f"https://dns.google/resolve?name={name}&type={rtype}")
    if status != 200:
        return None
    return [a.get("data", "").strip('"') for a in d.get("Answer", []) or []]


def rdap(domain):
    status, d = get_json(f"https://rdap.org/domain/{domain}")
    if status != 200:
        return {"error": f"RDAP HTTP {status}"}
    events = {e.get("eventAction"): e.get("eventDate") for e in d.get("events", [])}
    registrar, redacted = None, False
    for ent in d.get("entities", []):
        roles = ent.get("roles", [])
        vcard = ent.get("vcardArray", [None, []])[1]
        fn = next((v[3] for v in vcard if v and v[0] == "fn"), None)
        if "registrar" in roles:
            registrar = fn
        if "registrant" in roles and (not fn or "redacted" in str(fn).lower() or "privacy" in str(fn).lower()):
            redacted = True
    if any("redact" in json.dumps(r).lower() for r in d.get("remarks", [])) or d.get("redacted"):
        redacted = True
    return {"registrar": registrar, "created": events.get("registration"), "expires": events.get("expiration"),
            "status": d.get("status"), "nameservers": [n.get("ldhName", "").lower() for n in d.get("nameservers", [])],
            "registrant_details_hidden": redacted}


def main(domain):
    domain = domain.lower().removeprefix("https://").removeprefix("http://").split("/")[0].removeprefix("www.")
    r = {"domain": domain, "rdap": rdap(domain), "issues": [], "good": []}
    exp = r["rdap"].get("expires")
    if exp:
        days = (dt.datetime.fromisoformat(exp.replace("Z", "+00:00")) - dt.datetime.now(dt.timezone.utc)).days
        r["days_to_expiry"] = days
        if days < 30:
            r["issues"].append({"severity": "critical", "title": f"Domain expires in {days} days", "detail": "Confirm auto-renew and payment method."})
        elif days < 90:
            r["issues"].append({"severity": "medium", "title": f"Domain expires in {days} days", "detail": "Confirm auto-renew is on."})
    if r["rdap"].get("registrant_details_hidden") is False:
        r["issues"].append({"severity": "medium", "title": "Registrant details may be public", "detail": "Turn on WHOIS privacy at the registrar."})

    r["a"] = dns(domain, "A")
    mx = dns(domain, "MX") or []
    txt = dns(domain, "TXT") or []
    dmarc = [t for t in (dns("_dmarc." + domain, "TXT") or []) if t.lower().startswith("v=dmarc1")]
    spf = [t for t in txt if t.lower().startswith("v=spf1")]
    r["email"] = {"mx": mx, "spf": spf, "dmarc": dmarc,
                  "provider": next((p for k, p in {"google.com": "Google Workspace", "outlook.com": "Microsoft 365",
                                                   "zoho": "Zoho", "protonmail": "Proton", "icloud": "iCloud",
                                                   "secureserver": "GoDaddy", "mxroute": "MXroute", "fastmail": "Fastmail",
                                                   "mailchannels": "MailChannels (DreamHost mail)", "dreamhost": "DreamHost"}.items()
                                    if any(k in m.lower() for m in mx)), None)}
    if not mx:
        r["issues"].append({"severity": "medium", "title": "No email on the domain", "detail": "No MX records, so no name@domain address. Clients see a free-mail address instead."})
    if not spf:
        r["issues"].append({"severity": "high", "title": "No SPF record", "detail": "Anyone can send email that claims to be from this domain."})
    if not dmarc:
        r["issues"].append({"severity": "high", "title": "No DMARC record", "detail": "Spoofed email in the client's name won't be rejected. Add v=DMARC1; p=quarantine."})
    elif "p=none" in dmarc[0].lower():
        r["issues"].append({"severity": "low", "title": "DMARC is monitor-only (p=none)", "detail": "Move to p=quarantine once reports look clean."})
    else:
        r["good"].append("DMARC enforced")
    print(json.dumps(r, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
