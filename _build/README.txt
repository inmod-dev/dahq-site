The site's build + test tools (not pages). The two sign-in bounce pages come from ONE template:
  python _build/make_callbacks.py            writes qbo-callback.html + square-callback.html
  python _build/make_callbacks.py --check    fails if a page differs from the template
  <python with playwright> _build/test_callbacks.py   headless-browser test of both pages (Dark Age HQ's .venv has
                                              playwright + Chromium: requirements-dev.txt)
The connect / disconnect pages come from ONE template too (QuickBooks keeps connect.html + disconnect.html, the links
Intuit has on file; Square has square-connect.html + square-disconnect.html):
  python _build/make_connect.py              writes them (only a page that differs); --check fails if one differs
  python _build/test_pages.py                static test of every page (the template, the About page, links, nothing outside)
