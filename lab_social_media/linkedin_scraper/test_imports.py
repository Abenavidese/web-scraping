print("Testing Imports...")
try:
    import scrapers.linkedin_scraper
    print("✓ scrapers.linkedin_scraper imported")
except Exception as e:
    print(f"X scrapers.linkedin_scraper failed: {e}")

try:
    import utils.nlp_processor
    print("✓ utils.nlp_processor imported")
except Exception as e:
    print(f"X utils.nlp_processor failed: {e}")

try:
    import matplotlib
    print("✓ matplotlib imported")
    import matplotlib.pyplot
    print("✓ matplotlib.pyplot imported")
except Exception as e:
    print(f"X matplotlib failed: {e}")
