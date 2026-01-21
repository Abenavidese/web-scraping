from playwright.sync_api import sync_playwright
import time
import random

def random_sleep(min_seconds=2, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))

def run():
    print("Starting auto-login...")
    with sync_playwright() as p:
        # Use Microsoft Edge
        browser = p.chromium.launch(headless=False, channel="msedge")
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigating to Instagram...")
        page.goto("https://www.instagram.com/")
        random_sleep(3, 5)

        # Check for cookie dialog
        try:
             page.get_by_text("Allow all cookies").click(timeout=3000)
             print("Clicked cookie dialog.")
             random_sleep(1, 2)
        except:
             pass
        
        # Check if we are on the landing page that requires clicking "Log in"
        # Sometimes Instagram shows a landing page with a "Log in" text link
        try:
            # Look for inputs. If not found, look for "Log in" link
            if not page.locator('input[name="username"]').is_visible(timeout=5000):
                print("Username input not visible immediately. Looking for 'Log in' link...")
                # Search for typical links
                page.get_by_role("link", name="Log in").click()
                # Or try text selector
                # page.click("text=Log in")
                random_sleep(3, 5)
        except Exception as e:
            print(f"Navigation check debug: {e}")

        # Fill login form
        print("Entering credentials...")
        # Selectors for username and password often stable, but fallback to name attribute
        page.wait_for_selector('input[name="username"]', timeout=10000)
        page.fill('input[name="username"]', "antonioantonio12345656@gmail.com")
        random_sleep(1, 2)
        page.fill('input[name="password"]', "ANTONIO200-")
        random_sleep(1, 2)
        
        # Click login button
        print("Clicking login...")
        page.click('button[type="submit"]')
        
        # Wait for navigation or specific element that indicates login success
        # Usually checking for "Search" icon or profile picture
        print("Waiting for login to complete...")
        try:
            # Wait up to 15 seconds for a specific element that appears when logged in
            # svg[aria-label="Home"] or similar
            page.wait_for_selector('svg[aria-label="Inicio"]', timeout=15000) 
            # Note: aria-label might vary by language. "Inicio" for Spanish, "Home" for English.
            # We can also wait for url validation
        except:
            # Fallback check
            print("Warning: explicit wait timeout, checking URL or other indicators...")
            random_sleep(5, 8)
        
        # Check if we are logged in by URL or looking for "Save Info" modal
        if "accounts/onetap" in page.url:
            print("Detected 'Save Info' screen, clicking 'Not Now' if possible...")
            # Try to click "Not Now"
            try:
                page.get_by_text("Ahora no").click()
            except:
                pass
        
        # Final wait to ensure cookies are set
        try:
             page.wait_for_load_state('networkidle')
        except:
             pass
             
        random_sleep(3, 5)
        
        # Save state
        context.storage_state(path="auth.json")
        print("Session saved to 'auth.json'. Authenticated automatically.")
        
        browser.close()

if __name__ == "__main__":
    run()
