"""Static test of the site's pages (no browser needed). The connect / disconnect pages are exactly the template for every
service (QuickBooks keeps connect.html / disconnect.html, the links Intuit has on file, and its own words; Square has the same
two pages); the About page explains both services the same way; every page's own links point at a page that exists, and
no page loads anything from outside. Exits 1 on any failure.
  python _build/test_pages.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_connect as mk  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))
    if not ok:
        fails.append(name)


read = lambda n: open(os.path.join(mk.SITE, n), encoding="utf-8").read()   # noqa: E731
want = dict(mk.pages())
check("every connect / disconnect page is exactly the template (make_connect.py --check)",
      all(read(n).replace("\r\n", "\n") == p for n, p in want.items()), [n for n, p in want.items() if read(n).replace("\r\n", "\n") != p])
check("QuickBooks keeps its file names and words (Intuit's links); Square has the same two pages",
      "<h1>Connect QuickBooks</h1>" in read("connect.html") and "<h1>QuickBooks disconnected</h1>" in read("disconnect.html")
      and "access to your QuickBooks company" in read("disconnect.html")
      and "<h1>Connect Square</h1>" in read("square-connect.html") and "<h1>Square disconnected</h1>" in read("square-disconnect.html")
      and "access to your Square account" in read("square-disconnect.html")
      and "Settings → Connections → Square" in read("square-connect.html"))
idx = read("index.html")
check("the About page explains Square like QuickBooks: read only, never changes anything, how to connect",
      "<h2>How to connect QuickBooks</h2>" in idx and "<h2>How to connect Square</h2>" in idx
      and "It never changes anything in QuickBooks." in idx and "It never changes anything in Square." in idx
      and "Settings → Connections → Square</em>, and click <em>Connect</em>" in idx)
pages = sorted(f for f in os.listdir(mk.SITE) if f.endswith(".html"))
broken = [(f, h) for f in pages for h in re.findall(r'href="([^"#:]+)"', read(f)) if not os.path.exists(os.path.join(mk.SITE, h))]
check("every page's own links point at a page that exists", not broken, broken)
outside = [f for f in pages if re.search(r'\ssrc="https?:|<link[^>]+href="https?:|@import', read(f))]
check("no page loads anything from outside", not outside, outside)
print("\nALL PASSED" if not fails else f"\n{len(fails)} FAILED")
sys.exit(1 if fails else 0)
