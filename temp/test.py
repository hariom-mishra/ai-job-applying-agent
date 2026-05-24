import asyncio
import sys
import subprocess
import time

# Configuration
CDP_URL = "http://localhost:9222"

async def check_cdp_running():
    """Checks if Chrome is running with remote debugging enabled on port 9222."""
    import urllib.request
    try:
        urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=1)
        return True
    except Exception:
        return False

def get_first_job_url_via_applescript(platform="linkedin"):
    """
    Native macOS AppleScript extractor.
    Queries the active Chrome tab DOM and extracts the href of the first job card.
    """
    if platform == "linkedin":
        js_code = """
        (function() {
            var selectors = [
                'a[href*="currentJobId="]',
                'a[href*="/jobs/view/"]',
                'a[href*="/jobs/collections/"]',
                'li.jobs-search-results-list__list-item a.job-card-container__link',
                '.scaffold-layout__list-container li a.job-card-list__title',
                '.job-card-container a'
            ];
            for (var i = 0; i < selectors.length; i++) {
                var el = document.querySelector(selectors[i]);
                if (el && el.href) {
                    return el.href;
                }
            }
            return 'None';
        })()
        """
        url_match = "linkedin.com/jobs"
    else:  # naukri
        js_code = """
        (function() {
            var selectors = [
                'article.jobTuple a.title',
                'a.title.job-card-title',
                'article a[href*="/job-listings-"]',
                '.list article a'
            ];
            for (var i = 0; i < selectors.length; i++) {
                var el = document.querySelector(selectors[i]);
                if (el && el.href) {
                    return el.href;
                }
            }
            return 'None';
        })()
        """
        url_match = "naukri.com"
    
    # Escape double quotes for AppleScript syntax
    escaped_js = js_code.replace('"', '\\"').replace('\n', ' ')
    
    # Target the active tab of the frontmost window (which is the tab we just opened)
    applescript = f'''
    tell application "Google Chrome"
        tell active tab of window 1
            execute javascript "{escaped_js}"
        end tell
    end tell
    '''
    
    try:
        res = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, check=True)
        output = res.stdout.strip()
        return output
    except subprocess.CalledProcessError as e:
        print("\n🔒 Permission or Execution Error:")
        print(f"❌ Details: {e.stderr.strip() if e.stderr else e}")
        print("💡 To let the script click the job card automatically, please enable JavaScript for AppleScript:")
        print("   In Google Chrome's top menu bar, click: View -> Developer -> Allow JavaScript from Apple Events\n")
        return None

async def run_agent_workflow(platform="linkedin"):
    """
    Agent workflow (Playwright CDP): Connects over remote debugging port 9222.
    """
    try:
        from playwright.async_api import async_playwright
    except ModuleNotFoundError:
        print("❌ Error: 'playwright' is not installed in your Python environment.")
        print("💡 Install it for full agent mode: pip3 install playwright && playwright install")
        return

    url_map = {
        "linkedin": "https://www.linkedin.com/jobs/",
        "naukri": "https://www.naukri.com/"
    }
    target_url = url_map.get(platform, "linkedin")
    
    print(f"🔗 Connecting to your running Chrome profile over CDP ({CDP_URL})...")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]
            
            page = None
            for p_tab in context.pages:
                if platform in p_tab.url:
                    page = p_tab
                    print(f"🎯 Found an already active {platform} tab! Attaching...")
                    break
            
            if not page:
                page = await context.new_page()
                print(f"🌐 Navigating to {target_url}...")
                await page.goto(target_url, wait_until="load")
            
            print("⏳ Waiting for page elements to settle...")
            await page.wait_for_timeout(3000)
            
            if platform == "linkedin":
                selectors = [
                    "a[href*='currentJobId=']",
                    "a[href*='/jobs/view/']",
                    "a[href*='/jobs/collections/']",
                    "li.jobs-search-results-list__list-item a.job-card-container__link",
                    ".scaffold-layout__list-container li a.job-card-list__title"
                ]
                
                first_job = None
                for selector in selectors:
                    try:
                        first_job = page.locator(selector).first
                        if await first_job.count() > 0:
                            break
                    except Exception:
                        continue
                
                if first_job and await first_job.count() > 0:
                    job_title = await first_job.inner_text()
                    print(f"📌 Found first LinkedIn Job: '{job_title.split()[0]}'")
                    print("🖱️ Clicking first job card to open the details form...")
                    await first_job.click()
                    await page.wait_for_timeout(2000)
                    print("✅ Job details form loaded!")
                else:
                    print("⚠️ Could not find any job cards on the active LinkedIn page.")
            
            elif platform == "naukri":
                selectors = [
                    "article.jobTuple a.title",
                    "a.title.job-card-title",
                    "article a[href*='/job-listings-']"
                ]
                
                first_job = None
                for selector in selectors:
                    try:
                        first_job = page.locator(selector).first
                        if await first_job.count() > 0:
                            break
                    except Exception:
                        continue
                        
                if first_job and await first_job.count() > 0:
                    job_title = await first_job.inner_text()
                    print(f"📌 Found first Naukri Job: '{job_title}'")
                    print("🖱️ Clicking first Naukri job...")
                    await first_job.click()
                    await page.wait_for_timeout(2000)
                    print("✅ Job details form loaded!")
                else:
                    print("⚠️ Could not find any job cards on Naukri.")
                    
        except Exception as e:
            print(f"❌ Error during agent execution: {e}")

def open_fallback(platform="linkedin"):
    """Fallback method: Opens the URL and uses AppleScript to extract and open the job."""
    urls = {
        "linkedin": "https://www.linkedin.com/jobs/",
        "naukri": "https://www.naukri.com/"
    }
    url = urls.get(platform, "https://www.linkedin.com/jobs/")
    print(f"🚀 [Fallback Mode] Opening {platform} via standard macOS command...")
    subprocess.run(["open", "-a", "Google Chrome", url])
    
    # Retry loop: waits and attempts to extract up to 5 times (total 10 seconds)
    print("⏳ Waiting for the page to load in Chrome to extract the first job...")
    for attempt in range(1, 6):
        time.sleep(2)
        print(f"🍏 [AppleScript] Attempt {attempt}/5 to extract first job link...")
        job_url = get_first_job_url_via_applescript(platform)
        if job_url and job_url.startswith("http"):
            print(f"✅ Found job URL: {job_url}")
            print("🚀 Opening the job post in a new tab...")
            subprocess.run(["open", "-a", "Google Chrome", job_url])
            break
        elif job_url == "None" or not job_url:
            continue

async def main():
    if sys.platform != "darwin":
        print("⚠️ This script is designed for macOS (Darwin).")
        return
        
    platform = "linkedin"
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["naukri", "linkedin"]:
        platform = sys.argv[1].lower()
        
    cdp_active = await check_cdp_running()
    
    if cdp_active:
        await run_agent_workflow(platform)
    else:
        open_fallback(platform)

if __name__ == "__main__":
    asyncio.run(main())