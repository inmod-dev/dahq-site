"""square-callback.html in a real headless browser (Chromium via Playwright).

Run from the HQ repo's dev venv (playwright + its Chromium, requirements-dev.txt):
    "<HQ>\\.venv\\Scripts\\python.exe" tests\\test_square_callback.py
The page is served from this folder on 127.0.0.1; HQ's address (localhost:8878) is caught by the browser, never reached.
Exit code 0 = all passed.
"""
import base64
import functools
import hashlib
import http.server
import os
import re
import subprocess
import sys
import threading

from playwright.sync_api import sync_playwright

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "square-callback.html"
TARGET = "http://localhost:8878/square/callback"
fails = []


def check(name, ok, detail=None):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok or detail is None else f"  -> {detail}"))
    if not ok:
        fails.append(name)


src = open(os.path.join(SITE, PAGE), encoding="utf-8").read()
script = re.search(r"<script>(.*?)</script>", src, re.S).group(1)
csp = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', src).group(1)
want = "sha256-" + base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode()
check("strict CSP: default-src 'none', the ONE inline script allowed by its hash (which matches it), no base / form targets",
      csp == f"default-src 'none'; style-src 'unsafe-inline'; script-src '{want}'; base-uri 'none'; form-action 'none'", csp)
check("no outside scripts, styles, images or frames; one <script> only; keeps nothing (no storage, cookies or network calls)",
      src.count("<script") == 1 and not re.search(r"<(link|img|iframe|object|embed)\b|src=", src)
      and not re.search(r"localStorage|sessionStorage|indexedDB|cookie|fetch\(|XMLHttpRequest|sendBeacon|WebSocket", src))
check("the only web address it can send the browser to is HQ's own Square callback (+ the contact mail link)",
      set(re.findall(r"https?://[^\"'<> ]+", src)) == {TARGET} and 'name="referrer" content="no-referrer"' in src)
check("fallback link + a JS-off note",
      f'<a id="go" href="{TARGET}">' in src and "<noscript>" in src and "JavaScript is off" in src)
qbo_same = subprocess.run(["git", "-C", SITE, "diff", "--quiet", "HEAD", "--", "qbo-callback.html"]).returncode == 0
check("qbo-callback.html untouched", qbo_same)

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=SITE))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_address[1]}/{PAGE}"


def visit(br, query, js=True):
    """Open the page with this query; return (the HQ URL it forwarded to or None, every request URL, console errors, page)."""
    ctx = br.new_context(java_script_enabled=js)
    page, hit, reqs, errs = ctx.new_page(), [], [], []
    page.on("request", lambda r: reqs.append(r.url))
    page.on("console", lambda m: m.type == "error" and errs.append(m.text))
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.route("http://localhost:8878/**", lambda route: (hit.append(route.request.url),
                                                          route.fulfill(status=200, content_type="text/plain", body="HQ")))
    page.goto(BASE + query)
    if js:
        page.wait_for_url("http://localhost:8878/**", timeout=5000)
    else:
        page.wait_for_timeout(600)
    return (hit[0] if hit else None), reqs, errs, page, ctx


with sync_playwright() as pw:
    br = pw.chromium.launch()
    try:
        u, reqs, errs, _, ctx = visit(br, "?code=sq0cgp-CODE1&state=S%26x%3D1&response_type=code&realmId=R9&foo=bar")
        check("forwards ONLY code + state to exactly http://localhost:8878/square/callback (response_type, realmId, foo dropped; "
              "an '&' inside the state stays encoded)",
              u == TARGET + "?code=sq0cgp-CODE1&state=S%26x%3D1", u)
        check("in the browser: no CSP error (the hash lets the script run), no other request than the page itself and HQ",
              not errs and set(reqs) == {BASE + "?code=sq0cgp-CODE1&state=S%26x%3D1&response_type=code&realmId=R9&foo=bar", u}, (errs, reqs))
        ctx.close()
        u, *_, ctx = visit(br, "?error=access_denied&error_description=user%20denied&state=S2")
        check("a cancelled sign-in: error + error_description + state forwarded", u == TARGET + "?state=S2&error=access_denied&error_description=user+denied", u)
        ctx.close()
        u, *_, ctx = visit(br, "")
        check("no query -> plain HQ callback (HQ then says the sign-in doesn't match)", u == TARGET, u)
        ctx.close()
        u, reqs, _, page, ctx = visit(br, "?code=C&state=S", js=False)
        check("JavaScript off: nothing is forwarded, the note shows, the fallback link points at HQ's callback",
              u is None and "JavaScript is off" in page.inner_text("body") and page.get_attribute("#go", "href") == TARGET
              and all(not r.startswith("http://localhost:8878") for r in reqs), (u, reqs))
        ctx.close()
    finally:
        br.close()
        srv.shutdown()

print(f"\n{'ALL PASSED' if not fails else str(len(fails)) + ' FAILED'}")
sys.exit(1 if fails else 0)
