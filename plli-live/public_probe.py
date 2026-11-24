"""Inspect public rendered links only; no account, media download or alert."""
from playwright.sync_api import sync_playwright, TimeoutError
import re
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(locale="ko-KR")
    response = page.goto("https://weverse.io/plave/live?hl=ko", wait_until="domcontentloaded", timeout=30000)
    print("Public page HTTP:", response.status if response else "unknown")
    if not response or response.status >= 400:
        raise SystemExit("Public page unavailable")
    try:
        page.locator('a[href*="/plave/live/"]').first.wait_for(timeout=15000)
    except TimeoutError:
        pass
    cards = page.locator('a[href*="/plave/live/"]').evaluate_all("""nodes => nodes.slice(0,5).map(n=>({url:n.getAttribute('href'), text:n.innerText.slice(0,200), label:n.getAttribute('aria-label')}))""")
    print("Rendered public cards:", cards)
    print("Public heading:", page.title())
    browser.close()
    if not cards: raise SystemExit("No publicly rendered cards detected")
