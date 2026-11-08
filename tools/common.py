"""Shared HTTP helpers for SetPlay tools (standard library only)."""
import json
import os
import ssl
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (compatible; SetPlayAudit/1.0)"


def ssl_context():
    ctx = ssl.create_default_context()
    for var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        path = os.environ.get(var)
        if path and os.path.exists(path):
            ctx.load_verify_locations(path)
    if os.path.exists("/root/.ccr/ca-bundle.crt"):  # cloud session proxy CA
        ctx.load_verify_locations("/root/.ccr/ca-bundle.crt")
    return ctx


def request(url, method="GET", headers=None, data=None, timeout=30):
    """Return (status, headers, body_bytes). Never raises on HTTP errors."""
    h = {"User-Agent": UA, **(headers or {})}
    body = json.dumps(data).encode() if data is not None else None
    if body is not None:
        h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context()))
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read() if hasattr(e, "read") else b""
    except Exception as e:
        return None, {}, str(e).encode()


def get_json(url, **kw):
    status, _, body = request(url, **kw)
    try:
        return status, json.loads(body)
    except Exception:
        return status, {"_raw": body[:500].decode("utf-8", "replace")}
