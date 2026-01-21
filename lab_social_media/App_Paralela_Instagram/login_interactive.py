from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigating to Instagram...")
        page.goto("https://www.instagram.com/")
        
        print("\n" + "="*50)
        print("PLEASE LOG IN MANUALLY IN THE BROWSER WINDOW.")
        print("Once you are logged in and can see your feed, return here.")
        print("="*50 + "\n")
        
        input("Press Enter here after you have successfully logged in...")
        
        # Save storage state into the file.
        context.storage_state(path="auth.json")
        print("Session saved to 'auth.json'. You can now run the scraper.")
        
        browser.close()

if __name__ == "__main__":
    run()
