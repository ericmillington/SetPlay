#!/usr/bin/env python3
"""Automated website check for the Website Quality pillar.

Usage:  python3 tools/site_check.py https://example.com > site-check.json

Standard library only. Checks HTTPS/redirects, security headers, SEO and sharing
meta tags, basic accessibility signals, page weight, and third-party trackers.
It's a first pass and doesn't replace a manual review or PageSpeed Insights.
"""
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

UA = "Mozilla/5.0 (compatible; SetPlaySiteCheck/1.0)"
TIMEOUT = 20

# Hosts that indicate tracking/advertising. Their presence means a consent banner is
# likely legally required (GDPR/ePrivacy) and conflicts with our privacy principle.
TRACKERS = {
    "google-analytics.com": "Google Analytics",
    "googletagmanager.com": "Google Tag Manager",
    "doubleclick.net": "Google Ads / DoubleClick",
    "googleadservices.com": "Google Ads",
    "connect.facebook.net": "Meta Pixel",
    "facebook.com/tr": "Meta Pixel",
    "static.hotjar.com": "Hotjar",
    "snap.licdn.com": "LinkedIn Insight",
    "analytics.tiktok.com": "TikTok Pixel",
    "bat.bing.com": "Microsoft Ads",
    "static.ads-twitter.com": "X/Twitter Ads",
    "cdn.segment.com": "Segment",
    "js.hs-scripts.com": "HubSpot",
    "script.crazyegg.com": "Crazy Egg",
    "clarity.ms": "Microsoft Clarity",
    "pinimg.com/ct": "Pinterest Tag",
    "mc.yandex.ru": "Yandex Metrica",
}
PRIVACY_FRIENDLY = {
    "plausible.io": "Plausible",
    "usefathom.com": "Fathom",
    "cloudflareinsights.com": "Cloudflare Web Analytics",
    "simpleanalytics": "Simple Analytics",
    "umami": "Umami",
}
SECURITY_HEADERS = [
    "strict-transport-security",
    "content-security-policy",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
]
PLATFORM_HINTS = {
    "wp-content": "WordPress", "squarespace": "Squarespace", "wix.com": "Wix",
    "wixstatic": "Wix", "shopify": "Shopify", "webflow": "Webflow", "godaddy": "GoDaddy Builder",
    "weebly": "Weebly", "carrd.co": "Carrd", "framerusercontent": "Framer", 'content="ghost': "Ghost",
}


def ssl_context():
    ctx = ssl.create_default_context()
    for var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        path = os.environ.get(var)
        if path and os.path.exists(path):
            ctx.load_verify_locations(path)
    return ctx


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def fetch(url, follow=True):
    handlers = [urllib.request.HTTPSHandler(context=ssl_context())]
    if not follow:
        handlers.append(NoRedirect())
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    start = time.time()
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            body = r.read()
            return {"status": r.status, "url": r.geturl(), "headers": {k.lower(): v for k, v in r.headers.items()},
                    "body": body, "ms": int((time.time() - start) * 1000)}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "url": url, "headers": {k.lower(): v for k, v in e.headers.items()},
                "body": b"", "ms": int((time.time() - start) * 1000)}
    except Exception as e:  # network/TLS errors
        return {"status": None, "url": url, "headers": {}, "body": b"", "error": str(e), "ms": None}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lang = None
        self.title = ""
        self._in_title = False
        self.meta = {}
        self.links = []
        self.h1 = 0
        self.headings = []
        self.imgs = 0
        self.imgs_no_alt = 0
        self.scripts = []
        self.anchors = []
        self.forms = 0
        self.inputs_unlabelled = 0
        self._labels_for = set()
        self._input_ids = []

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang") or None
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key.lower()] = a.get("content", "")
        elif tag == "link":
            self.links.append(a)
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings.append(tag)
            if tag == "h1":
                self.h1 += 1
        elif tag == "img":
            self.imgs += 1
            if "alt" not in a:
                self.imgs_no_alt += 1
        elif tag == "script" and a.get("src"):
            self.scripts.append(a["src"])
        elif tag == "a" and a.get("href"):
            self.anchors.append(a["href"])
        elif tag == "form":
            self.forms += 1
        elif tag == "label" and a.get("for"):
            self._labels_for.add(a["for"])
        elif tag in ("input", "textarea", "select"):
            if a.get("type") in ("hidden", "submit", "button"):
                return
            if not (a.get("aria-label") or a.get("aria-labelledby")):
                self._input_ids.append(a.get("id"))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data

    def close(self):
        super().close()
        self.inputs_unlabelled = sum(1 for i in self._input_ids if not i or i not in self._labels_for)


def check(url):
    if "://" not in url:
        url = "https://" + url
    host = urlparse(url).netloc
    issues, good = [], []

    page = fetch(url)
    result = {"url": url, "checked_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "reachable": page["status"] == 200}
    if page.get("error") or page["status"] != 200:
        result["error"] = page.get("error") or f"HTTP {page['status']}"
        result["issues"] = [{"severity": "high", "title": "Site not reachable", "detail": result["error"]}]
        return result

    final = page["url"]
    result["final_url"] = final
    result["response_ms"] = page["ms"]
    h = page["headers"]

    # HTTPS
    https = final.startswith("https://")
    if https:
        good.append("Served over HTTPS")
    else:
        issues.append({"severity": "high", "title": "Not served over HTTPS", "detail": "Browsers show 'Not secure'."})
    http_probe = fetch(f"http://{host}/", follow=False)
    loc = http_probe["headers"].get("location", "")
    redirects = http_probe["status"] in (301, 302, 307, 308) and loc.startswith("https://")
    if http_probe["status"] is None:
        redirects = None  # couldn't connect over plain http (network/proxy); verify by hand
    result["http_redirects_to_https"] = redirects
    if redirects is False and https:
        issues.append({"severity": "medium", "title": "http:// doesn't redirect to https://", "detail": f"http status {http_probe['status']}"})

    # Security headers
    present = {k: (k in h) for k in SECURITY_HEADERS}
    result["security_headers"] = present
    missing = [k for k, v in present.items() if not v]
    if missing:
        issues.append({"severity": "low" if len(missing) < 3 else "medium", "title": "Missing security headers", "detail": ", ".join(missing)})
    result["server"] = h.get("server")

    # Parse HTML
    html = page["body"].decode("utf-8", errors="replace")
    p = PageParser()
    p.feed(html)
    p.close()

    title = " ".join(p.title.split())
    desc = p.meta.get("description", "")
    result["seo"] = {
        "title": title, "title_length": len(title),
        "meta_description": desc, "description_length": len(desc),
        "canonical": next((l.get("href") for l in p.links if "canonical" in l.get("rel", "")), None),
        "robots_meta": p.meta.get("robots"),
        "h1_count": p.h1,
    }
    if not title:
        issues.append({"severity": "high", "title": "Missing page title", "detail": "Title is what shows in search results."})
    elif not 15 <= len(title) <= 65:
        issues.append({"severity": "low", "title": "Title length not ideal", "detail": f"{len(title)} chars (aim 15–65): “{title}”"})
    if not desc:
        issues.append({"severity": "medium", "title": "Missing meta description", "detail": "Search engines will make one up."})
    elif not 50 <= len(desc) <= 160:
        issues.append({"severity": "low", "title": "Meta description length not ideal", "detail": f"{len(desc)} chars (aim 50–160)"})
    if p.h1 != 1:
        issues.append({"severity": "low", "title": f"Page has {p.h1} H1 headings", "detail": "Use exactly one H1."})
    if "noindex" in (p.meta.get("robots") or "").lower():
        issues.append({"severity": "critical", "title": "Home page is set to noindex", "detail": "It is hidden from search engines."})

    og = {k: p.meta.get(k) for k in ("og:title", "og:description", "og:image", "twitter:card")}
    result["social_preview"] = og
    if not og["og:image"] or not og["og:title"]:
        issues.append({"severity": "medium", "title": "Incomplete social preview tags", "detail": "Links shared on social/messages will look bare."})

    # Mobile & accessibility signals
    viewport = p.meta.get("viewport")
    result["accessibility"] = {
        "lang": p.lang, "viewport": viewport, "images": p.imgs, "images_missing_alt": p.imgs_no_alt,
        "unlabelled_form_fields": p.inputs_unlabelled, "heading_order": p.headings[:20],
    }
    if not viewport:
        issues.append({"severity": "high", "title": "No mobile viewport", "detail": "Likely renders poorly on phones."})
    if not p.lang:
        issues.append({"severity": "medium", "title": "Missing lang attribute", "detail": "Screen readers can't pick the right voice."})
    if p.imgs_no_alt:
        issues.append({"severity": "medium", "title": f"{p.imgs_no_alt} of {p.imgs} images missing alt text", "detail": "Invisible to screen-reader users and to image search."})
    if p.inputs_unlabelled:
        issues.append({"severity": "medium", "title": f"{p.inputs_unlabelled} form fields without labels", "detail": "Hard to use with assistive tech."})

    # Scripts, trackers, platform
    script_hosts = sorted({urlparse(urljoin(final, s)).netloc for s in p.scripts} - {"", urlparse(final).netloc})
    found_trackers = sorted({name for pat, name in TRACKERS.items() if pat in html})
    friendly = sorted({name for pat, name in PRIVACY_FRIENDLY.items() if pat in html})
    platform = sorted({name for pat, name in PLATFORM_HINTS.items() if pat in html.lower()})
    result["third_party_script_hosts"] = script_hosts
    result["trackers"] = found_trackers
    result["privacy_friendly_analytics"] = friendly
    result["platform_hints"] = platform
    result["generator"] = p.meta.get("generator")
    if found_trackers:
        issues.append({"severity": "medium", "title": f"{len(found_trackers)} third-party tracker(s)", "detail": ", ".join(found_trackers)})
    else:
        good.append("No known ad/analytics trackers")

    # Weight
    kb = round(len(page["body"]) / 1024, 1)
    result["html_kb"] = kb
    result["script_count"] = len(p.scripts)
    if kb > 300:
        issues.append({"severity": "low", "title": f"Heavy HTML ({kb} KB)", "detail": "Often a sign of builder bloat."})
    if len(p.scripts) > 15:
        issues.append({"severity": "low", "title": f"{len(p.scripts)} external scripts", "detail": "Slows load; review what's needed."})

    # Copyright freshness
    year = time.gmtime().tm_year
    for y in range(year - 10, year - 1):
        if f"© {y}" in html or f"&copy; {y}" in html or f"Copyright {y}" in html:
            issues.append({"severity": "low", "title": f"Stale copyright year ({y})", "detail": "Signals an unmaintained site."})
            break

    # robots / sitemap
    base = f"{urlparse(final).scheme}://{urlparse(final).netloc}"
    result["robots_txt"] = fetch(base + "/robots.txt")["status"] == 200
    result["sitemap_xml"] = fetch(base + "/sitemap.xml")["status"] == 200
    if not result["sitemap_xml"]:
        issues.append({"severity": "low", "title": "No sitemap.xml", "detail": "Helps search engines find every page."})

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    result["issues"] = sorted(issues, key=lambda i: order[i["severity"]])
    result["good"] = good
    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    print(json.dumps(check(sys.argv[1]), indent=2, ensure_ascii=False))
