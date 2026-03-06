from playwright.sync_api import sync_playwright
import time

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()
        page.goto("https://www.instagram.com/p/CpTedtar1Nr/")
        time.sleep(5)
        
        with open("out.txt", "w", encoding="utf-8") as f:
            main_elem = page.locator('main')
            if main_elem.count() > 0:
                 f.write(main_elem.nth(0).inner_text() + "\n")
            else:
                 f.write(page.evaluate('document.body.innerText'))
                 
        browser.close()

if __name__ == "__main__":
    test()
