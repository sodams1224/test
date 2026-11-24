"""Local browser diagnostic. No secrets exported; no notification sent.
Use only if automated access is permitted. Do not run on public CI.
"""
from playwright.sync_api import sync_playwright
from notification_filter import parse_card

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="ko-KR", timezone_id="Asia/Seoul")
        page = context.new_page()
        page.goto("https://weverse.io/plave/live?hl=ko")
        input("In the browser, sign in yourself and open PLAVE notifications. Press Enter here to check once: ")
        if not page.url.startswith("https://weverse.io/"):
            raise SystemExit("Open official Weverse notifications first.")
        cards = page.get_by_text("LIVE를 시작했습니다", exact=False).evaluate_all("""nodes => {
          const results = new Set();
          for (const n of nodes) {
            for (let el=n; el && el!==document.body; el=el.parentElement) {
              const t=el.innerText || "";
              if (t.length>500) break;
              if (t.includes("LIVE를 시작했습니다") && /PLAVE\\s*[·・]\\s*\\d{4}\\.\\d{2}\\.\\d{2}\\s+\\d{2}:\\d{2}/.test(t)) {
                results.add(t);
                break;
              }
            }
          }
          return [...results];
        }""")
        found = [e for card in cards if (e:=parse_card(card))]
        print("Matched PLAVE live notifications:", len({e["id"] for e in found}))
        print("Dry run only. No account details or messages sent.")
        browser.close()
if __name__ == "__main__":
    main()
