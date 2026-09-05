import os
import time
import subprocess
import requests
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.join(os.getcwd(), "docs", "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def wait_for_server(url: str, timeout: int = 30) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code in [200, 404]:
                return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    print("Starting server for high-resolution table capture...")
    server_process = subprocess.Popen(
        [os.path.join(os.getcwd(), ".venv", "Scripts", "python.exe"), "-m", "uvicorn", "backend.main:app", "--port", "8000", "--host", "127.0.0.1"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    try:
        if not wait_for_server("http://127.0.0.1:8000/api/health", timeout=30):
            print("Failed to reach server")
            return

        print("Server up! Launching Playwright...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})

            page.goto("http://127.0.0.1:8000")
            page.wait_for_timeout(3000)

            # 1. Data Sources View
            print("Capturing data_sources.png with element wait...")
            page.locator("aside button", has_text="Data Warehouse").click()
            page.wait_for_selector("text=rows", timeout=30000)
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "data_sources.png"), full_page=True)

            # 2. Semantic Catalog View
            print("Capturing data_catalog.png with element wait...")
            page.locator("aside button", has_text="Semantic Catalog").click()
            page.wait_for_selector("text=cols", timeout=30000)
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "data_catalog.png"), full_page=True)

            browser.close()
            print("Both data_sources.png and data_catalog.png captured successfully!")
    finally:
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    main()
