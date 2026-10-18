"""The connect / disconnect pages, ONE template for every service (2026-10-18: Square added, matching QuickBooks).
QuickBooks keeps its own file names (connect.html, disconnect.html: the links Intuit has on file) and its exact words;
Square gets the same two pages (square-connect.html, square-disconnect.html). A page is written only when it differs from
the template (CRLF = the same page), so an unchanged page never moves.
  python _build/make_connect.py           writes the pages
  python _build/make_connect.py --check   exits 1 if a page on disk differs from the template (tests use it)
"""
import os
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICES = [
    {"service": "QuickBooks", "account": "QuickBooks company", "connect": "connect.html", "disconnect": "disconnect.html"},
    {"service": "Square", "account": "Square account", "connect": "square-connect.html", "disconnect": "square-disconnect.html"},
]
HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} — Dark Age HQ</title>
<style>body{{font:16px/1.6 Georgia,serif;max-width:720px;margin:40px auto;padding:0 16px;color:#222;background:#fff}}h1{{font-size:28px}}h2{{font-size:19px;margin-top:28px}}nav a{{margin-right:14px}}.note{{background:#f4f1e8;padding:10px 14px;border-left:3px solid #b08d3c}}</style></head><body>
<nav><a href="index.html">Dark Age HQ</a><a href="eula.html">License</a><a href="privacy.html">Privacy</a></nav>
"""
FOOT = """<hr><p>Dark Age HQ is made by Greysen Fox (operating as iNMod.), Argyle, Texas. Contact: <a href="mailto:contact@inmod.dev">contact@inmod.dev</a></p></body></html>
"""
CONNECT = """<h1>Connect {service}</h1>
<p>Dark Age HQ is a desktop app, so {service} is connected from inside the app.</p>
<ol><li>Open Dark Age HQ on your computer.</li><li>Go to <em>Settings → Connections → {service}</em>.</li><li>Click <em>Connect</em> (or <em>Sign in again</em>), sign in to {service}, and approve access.</li></ol>
<p>You can close this page.</p>
"""
DISCONNECT = """<h1>{service} disconnected</h1>
<p>Dark Age HQ no longer has access to your {account}. The app has stopped reading {service} data. If you disconnected from inside the app, its saved {service} sign-in has also been deleted from your computer.</p>
<p>To reconnect, open Dark Age HQ and go to <em>Settings → Connections → {service} → Connect</em>.</p>
"""


def pages():
    for s in SERVICES:
        yield s["connect"], HEAD.format(title="Connect") + CONNECT.format(**s) + FOOT
        yield s["disconnect"], HEAD.format(title="Disconnected") + DISCONNECT.format(**s) + FOOT


def main():
    bad = []
    for name, page in pages():
        path = os.path.join(SITE, name)
        same = os.path.exists(path) and open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n") == page
        if "--check" in sys.argv:
            if not same:
                bad.append(name)
        elif not same:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(page)
            print("wrote", name)
    if bad:
        sys.exit("differs from the template: " + ", ".join(bad))


if __name__ == "__main__":
    main()
