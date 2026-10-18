"""The sign-in bounce pages (QuickBooks + Square production redirects): ONE template, one list of services (2026-10-18).
Each page hands Intuit's / Square's redirect straight back to Dark Age HQ on the owner's own computer: it forwards ONLY its
service's sign-in keys to exactly http://localhost:8878/<service>/callback, keeps nothing, loads nothing from outside
(strict CSP: the one inline script allowed by its sha256 hash), logs nothing, sends no referrer, has a fallback link and a
JavaScript-off note, in the site's own look.
  python _build/make_callbacks.py           writes the pages
  python _build/make_callbacks.py --check   exits 1 if a page on disk differs from the template (tests use it)
"""
import base64
import hashlib
import json
import os
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = [
    {"file": "qbo-callback.html", "service": "QuickBooks", "target": "http://localhost:8878/qbo/callback",
     "keys": ["code", "state", "realmId", "error", "error_description"]},
    {"file": "square-callback.html", "service": "Square", "target": "http://localhost:8878/square/callback",
     "keys": ["code", "state", "error", "error_description"]},
]
SCRIPT = ('(function(){var T="%s",K=%s,i=new URLSearchParams(location.search),o=new URLSearchParams();K.forEach(function(k)'
          '{var v=i.get(k);if(v!==null)o.set(k,v)});var u=T+(o.toString()?"?"+o.toString():"");document.getElementById("go").href=u;'
          'location.replace(u)})();')
TEMPLATE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><meta name="robots" content="noindex">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-{hash}'; base-uri 'none'; form-action 'none'">
<title>Returning to Dark Age HQ</title>
<style>body{{font:16px/1.6 Georgia,serif;max-width:720px;margin:40px auto;padding:0 16px;color:#222;background:#fff}}h1{{font-size:28px}}.note{{background:#f4f1e8;padding:10px 14px;border-left:3px solid #b08d3c}}</style></head><body>
<h1>Returning you to Dark Age HQ…</h1>
<p class="note">{service} has finished. This page hands the sign-in straight back to Dark Age HQ on this computer. It keeps nothing.</p>
<p>If nothing happens, <a id="go" href="{target}">continue to Dark Age HQ</a> (Dark Age HQ must be open on this computer).</p>
<noscript><p>JavaScript is off, so this page can't pass the sign-in on. Turn it on, or press Connect in Dark Age HQ again.</p></noscript>
<hr><p>Dark Age HQ is made by Greysen Fox (operating as iNMod.), Argyle, Texas. Contact: <a href="mailto:contact@inmod.dev">contact@inmod.dev</a></p>
<script>{script}</script>
</body></html>
"""


def render(p):
    script = SCRIPT % (p["target"], json.dumps(p["keys"], separators=(",", ":")))
    h = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode("ascii")
    return TEMPLATE.format(hash=h, service=p["service"], target=p["target"], script=script)


def main():
    bad = []
    for p in PAGES:
        path, page = os.path.join(SITE, p["file"]), render(p)
        if "--check" in sys.argv:
            if not os.path.exists(path) or open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n") != page:   # CRLF = same page
                bad.append(p["file"])
        else:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(page)
            print("wrote", p["file"])
    if bad:
        sys.exit("differs from the template: " + ", ".join(bad))


if __name__ == "__main__":
    main()
