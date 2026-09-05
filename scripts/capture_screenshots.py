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
    print("Starting OpsPilot backend server on port 8000...")
    log_file = open("server.log", "w")
    server_process = subprocess.Popen(
        [os.path.join(os.getcwd(), ".venv", "Scripts", "python.exe"), "-m", "uvicorn", "backend.main:app", "--port", "8000", "--host", "127.0.0.1"],
        stdout=log_file,
        stderr=subprocess.STDOUT
    )

    try:
        print("Waiting for server...")
        if not wait_for_server("http://127.0.0.1:8000/api/health", timeout=30):
            print("Server failed to respond within 30s")
            log_file.close()
            with open("server.log", "r") as f:
                print("Server log:\n", f.read())
            return

        print("Server is UP! Launching Playwright...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

            page.on("console", lambda msg: print(f"[CONSOLE] {msg.type}: {msg.text}"))
            page.on("pageerror", lambda exc: print(f"[PAGE ERROR] {exc}"))

            page.goto("http://127.0.0.1:8000")
            page.wait_for_timeout(3000)

            # 1. Dashboard View
            print("Capturing dashboard.png...")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "dashboard.png"), full_page=True)

            # 2. Operations Copilot View
            print("Capturing copilot_analysis.png...")
            page.locator("aside button", has_text="Operations Copilot").click()
            page.wait_for_timeout(1500)
            try:
                page.fill("input[placeholder*='Ask anything']", "Which orders are delayed and what are the carrier causes?")
                page.click("button:has(svg.lucide-send)")
                page.wait_for_timeout(4000)
            except Exception as e:
                print(f"Copilot query error: {e}")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "copilot_analysis.png"), full_page=True)

            # 3. Data Warehouse View
            print("Capturing data_sources.png...")
            page.locator("aside button", has_text="Data Warehouse").click()
            page.wait_for_timeout(2000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "data_sources.png"), full_page=True)

            # 4. Semantic Data Catalog View
            print("Capturing data_catalog.png...")
            page.locator("aside button", has_text="Semantic Catalog").click()
            page.wait_for_timeout(2000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "data_catalog.png"), full_page=True)

            # 5. KPIs & Metrics View
            print("Capturing metrics.png...")
            page.locator("aside button", has_text="KPIs & Metrics").click()
            page.wait_for_timeout(2000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "metrics.png"), full_page=True)

            # 6. Exceptions & SLA Monitor View
            print("Capturing exceptions.png...")
            page.locator("aside button", has_text="Exceptions & SLA").click()
            page.wait_for_timeout(2000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "exceptions.png"), full_page=True)

            # 7. Action Center View
            print("Capturing action_center.png...")
            page.locator("aside button", has_text="Action Center").click()
            page.wait_for_timeout(2000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "action_center.png"), full_page=True)

            # 8. Workflow Studio View
            print("Capturing workflow.png...")
            page.locator("aside button", has_text="Workflow Studio").click()
            page.wait_for_timeout(2000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "workflow.png"), full_page=True)

            # 9. Knowledge Base View
            print("Capturing knowledge_base.png...")
            page.locator("aside button", has_text="Knowledge Base").click()
            page.wait_for_timeout(2000)
            try:
                page.fill("input[placeholder*='Search operational policies']", "credit hold policy")
                page.click("button:has-text('Search Policies')")
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Knowledge base search error: {e}")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "knowledge_base.png"), full_page=True)

            # 10. Reports & Exports View
            print("Capturing executive_report.png...")
            page.locator("aside button", has_text="Reports & Exports").click()
            page.wait_for_timeout(2000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "executive_report.png"), full_page=True)

            # 11. Audit & Safety View
            print("Capturing audit_log.png...")
            page.locator("aside button", has_text="Audit & Safety").click()
            page.wait_for_timeout(2000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "audit_log.png"), full_page=True)

            # 12. Morning Operations Review Modal (captured last to prevent any modal backdrop overlap)
            print("Capturing morning_review.png...")
            page.locator("aside button", has_text="Dashboard").click()
            page.wait_for_timeout(1000)
            page.click("button:has-text('Morning Operations Review')")
            try:
                page.wait_for_selector("text=Daily Morning Operations Review", timeout=15000)
                page.wait_for_timeout(1500)
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "morning_review.png"), full_page=True)
                page.click("button:has-text('Acknowledge & Close')")
                page.wait_for_timeout(1000)
            except Exception as e:
                print(f"Morning review capture notice: {e}")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "morning_review.png"), full_page=True)

            browser.close()
            print("All 12 screenshots successfully captured!")
    finally:
        server_process.terminate()
        server_process.wait()
        print("Server process terminated.")

if __name__ == "__main__":
    main()
