"""
One-time inspect: buksan e-magazine page gamit Playwright at i-print ang actual href
at HTML ng bawat "Read" at "Download" link para ma-check natin ang structure.
Run: python inspect_emagazine_links.py
"""
from playwright.sync_api import sync_playwright
import json

URL = "https://www.philrice.gov.ph/e-magazine/"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(20000)
        print(f"Loading {URL} ...")
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Lahat ng link na may text Read o Download
        links_info = []
        for a in page.locator("a[href]").all():
            text = (a.inner_text() or "").strip()
            href = a.get_attribute("href")
            if not href:
                continue
            if "read" not in text.lower() and "download" not in text.lower():
                continue
            # Outer HTML (truncated)
            try:
                html = a.evaluate("el => el.outerHTML").strip()[:500]
            except Exception:
                html = ""
            links_info.append({
                "text": text,
                "href": href,
                "html_sample": html,
            })
            print("-" * 60)
            print(f"Text: {text!r}")
            print(f"href: {href}")
            print(f"HTML: {html[:400]}...")
            print()

        print("=" * 60)
        print(f"Total Read/Download links: {len(links_info)}")
        # I-save din as JSON
        with open("emagazine_links_inspect.json", "w", encoding="utf-8") as f:
            json.dump(links_info, f, indent=2, ensure_ascii=False)
        print("Saved to emagazine_links_inspect.json")

        browser.close()

if __name__ == "__main__":
    main()
