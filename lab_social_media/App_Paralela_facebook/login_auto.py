from playwright.sync_api import sync_playwright
import time
import random

def random_sleep(min_seconds=2, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))

def run():
    print("Starting Facebook auto-login...")
    with sync_playwright() as p:
        # Use Microsoft Edge channel if available, or chromium
        browser = p.chromium.launch(headless=False, channel="msedge")
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigating to Facebook...")
        page.goto("https://www.facebook.com/")
        random_sleep(3, 5)

        # Handle cookies if present (Approximation for common dialogues)
        try:
            # Look for "Allow all cookies" or similar buttons
            # Selector is tricky as it varies by region. 
            # Often it's a button with specific text or testid.
            cookie_btn = page.query_selector('button[data-cookiebanner="accept_button"]')
            if cookie_btn:
                cookie_btn.click()
                print("Clicked cookie banner.")
                random_sleep(2, 3)
            else:
                # Try by text for Spanish/English
                page.get_by_text("Permitir todas las cookies").click(timeout=2000)
        except:
            pass

        # Check if already logged in (unlikely in fresh context but good practice)
        if page.locator('input[name="email"]').is_visible():
            print("Entering credentials...")
            
            # Fill email
            page.fill('input[name="email"]', "jxuxhdjdsjn23@gmail.com")
            random_sleep(1, 2)
            
            # Fill pass
            page.fill('input[name="pass"]', "xxKPeYAEI00fohS")
            random_sleep(1, 2)
            
            # Click login
            print("Clicking login...")
            page.click('button[name="login"]')
            
            # Wait for navigation
        # Wait for navigation
            try:
                page.wait_for_navigation(timeout=15000)
            except:
                print("Wait for navigation timeout, checking state...")

            random_sleep(3, 5)
            
        # Manual Confirmation Step (Crucial for stability)
        print("\n" + "="*50)
        print("IMPORTANTE: Observa la ventana del navegador.")
        print("1. Si te pide verificación, código o captcha, resuélvelo manualmente.")
        print("2. Espera hasta que veas tu muro de noticias (Feed) de Facebook.")
        print("="*50)
        input(">>> Cuando veas el muro de Facebook, presiona ENTER aquí para continuar...")

        # Check login success (Secondary check)
        if not page.locator('input[name="email"]').is_visible():
            print("Login confirmado.")
            
            # Save state
            context.storage_state(path="auth_fb.json")
            print("Session saved to 'auth_fb.json'.")
        else:
            print("\n!!! ATENCIÓN REQUERIDA !!!")
            print("El login automático no pudo completarse (Facebook pide verificación o 2FA).")
            print("Por favor, completa el inicio de sesión MANUALMENTE en el navegador que se abrió.")
            input("Una vez que veas tu muro/feed de Facebook, presiona ENTER aquí en la terminal para guardar la sesión...")
            
            # Save state after manual intervention
            context.storage_state(path="auth_fb.json")
            print("Sesión guardada manualmente en 'auth_fb.json'.")
            
        browser.close()

if __name__ == "__main__":
    run()
