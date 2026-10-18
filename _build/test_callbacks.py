"""Headless-browser test of the sign-in bounce pages (Playwright + its Chromium; dev only). For each page: it forwards ONLY its
service's keys (in order, values intact) to exactly its HQ callback; it fetches nothing else (no outside request, no storage,
no logging); its CSP lets its one script run and nothing more; JavaScript off -> the note shows and the fallback link is the
bare callback; no query -> the bare callback. Exits 1 on any failure.
  <python with playwright> _build/test_callbacks.py
"""
import os
import pathlib
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_callbacks as mc  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))
    if not ok:
        fails.append(name)


check("both pages are exactly the template (make_callbacks.py --check)",
      all(open(os.path.join(mc.SITE, p["file"]), encoding="utf-8", newline="").read().replace("\r\n", "\n") == mc.render(p) for p in mc.PAGES))
SENT = {"code": "C-123 &x", "state": "S/456", "realmId": "9130", "error": "access_denied", "error_description": "no thanks",
        "response_type": "code", "evil": "<script>", "next": "https://example.com"}
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for p in mc.PAGES:
        url = pathlib.Path(os.path.join(mc.SITE, p["file"])).as_uri()
        src = open(os.path.join(mc.SITE, p["file"]), encoding="utf-8").read()
        for label, query in (("full", SENT), ("none", {})):
            ctx = br.new_context()
            seen, hits, errs = [], [], []
            ctx.on("request", lambda r: seen.append(r.url))
            ctx.route("http://localhost:8878/**", lambda route: (hits.append(route.request.url), route.fulfill(status=200, body="ok")))
            pg = ctx.new_page()
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.goto(url + ("?" + urllib.parse.urlencode(query) if query else ""))
            pg.wait_for_timeout(500)
            want = {k: query[k] for k in p["keys"] if k in query}
            exp = p["target"] + ("?" + urllib.parse.urlencode(want) if want else "")
            got = hits[0] if hits else None
            check(f"{p['file']} ({label} query): forwards ONLY {', '.join(p['keys'])} to exactly {p['target']}",
                  got is not None and urllib.parse.urlsplit(got)._replace(query="").geturl() == p["target"]
                  and urllib.parse.parse_qsl(urllib.parse.urlsplit(got).query) == list(want.items()), (got, exp))
            check(f"{p['file']} ({label}): no other request (only the page itself + the hand-back), no console errors (CSP lets its one script run)",
                  all(u.startswith("file:") or u.startswith(p["target"]) for u in seen) and not errs, (seen, errs))
            ctx.close()
        ctx = br.new_context(java_script_enabled=False)
        pg = ctx.new_page()
        pg.goto(url + "?" + urllib.parse.urlencode(SENT))
        check(f"{p['file']}: JavaScript off -> the note shows, nothing moves, the fallback link is the bare callback",
              "JavaScript is off" in pg.inner_text("body") and pg.get_attribute("#go", "href") == p["target"] and pg.url.startswith("file:"))
        ctx.close()
        csp = re.search(r'Content-Security-Policy" content="([^"]+)"', src)
        check(f"{p['file']}: strict CSP (default-src 'none', the script by hash only, no base / forms), no referrer, noindex; nothing "
              "kept or logged (no storage, cookies, fetch, XHR, beacons or console); no outside file; the site's footer + contact",
              csp and "default-src 'none'" in csp.group(1) and "script-src 'sha256-" in csp.group(1) and "unsafe-eval" not in csp.group(1)
              and "base-uri 'none'" in csp.group(1) and "form-action 'none'" in csp.group(1)
              and '<meta name="referrer" content="no-referrer">' in src and 'content="noindex"' in src
              and not re.search(r"localStorage|sessionStorage|document\.cookie|fetch\(|XMLHttpRequest|sendBeacon|console\.", src)
              and not re.search(r'\ssrc=|<link|@import', src)
              and "contact@inmod.dev" in src and f"{p['service']} has finished." in src, csp and csp.group(1))
    br.close()
print("\nALL PASSED" if not fails else f"\n{len(fails)} FAILED")
sys.exit(1 if fails else 0)
