"""Capture README screenshots of a running app (``streamlit run src/app.py``).

Uses the locally installed Microsoft Edge through Playwright, so no browser download is needed:
    pip install playwright && python docs/take_screenshots.py [http://localhost:8501]
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
OUT = Path(__file__).resolve().parent / "screenshots"
QUERY = "detecting misinformation on social media"

OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    for scheme in ("light",):
        page = browser.new_page(viewport={"width": 1400, "height": 1100}, color_scheme=scheme)
        page.goto(URL)
        box = page.get_by_placeholder("e.g. transfer learning")
        box.wait_for(timeout=120_000)
        box.fill(QUERY)
        box.press("Enter")
        page.get_by_text("results for").wait_for(timeout=60_000)
        page.wait_for_timeout(1500)
        page.screenshot(path=OUT / f"search_{scheme}.png")
        page.close()
    browser.close()
print(f"Saved screenshots to {OUT}")
