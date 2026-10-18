The site's build + test tools (not pages). The two sign-in bounce pages come from ONE template:
  python _build/make_callbacks.py            writes qbo-callback.html + square-callback.html
  python _build/make_callbacks.py --check    fails if a page differs from the template
  <python with playwright> _build/test_callbacks.py   headless-browser test of both pages (Dark Age HQ's .venv has
                                              playwright + Chromium: requirements-dev.txt)
