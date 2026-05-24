"""Fetches LinkedIn job listings and populates state with structured Job objects."""
import os
import subprocess
import time
import urllib.request

from playwright.sync_api import sync_playwright

from app.models.job import Job
from app.models.state import JobApplicationState
from app.services.job_extractor import extract_job_fields
from app.services.linkedin_scraper import scrape_job_description, scrape_job_listings

CDP_URL = "http://localhost:9222"
LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/"


def _is_cdp_running() -> bool:
    try:
        urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=1)
        return True
    except Exception:
        return False


def job_fetcher_agent(state: JobApplicationState):
    print("job fetcher agent running...")

    role = state.profile.looking_for
    location = state.profile.location
    jobs = []

    if not _is_cdp_running():
        print("CDP not active — launching Chrome with a dedicated agent profile...")
        try:
            profile_dir = "/Users/hariommishra/Desktop/dev/ai/ai-job-application-agent/chrome_profile"
            subprocess.Popen([
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "--remote-debugging-port=9222",
                f"--user-data-dir={profile_dir}"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Failed to start Chrome via subprocess: {e}")

        # Wait and poll for up to 8 seconds
        cdp_ready = False
        for i in range(8):
            print(f"Checking if Chrome CDP is ready (attempt {i+1}/8)...")
            time.sleep(1)
            if _is_cdp_running():
                cdp_ready = True
                break

        if not cdp_ready:
            print("\n❌ Failed to connect to the Chrome agent profile.")
            print("👉 Please verify that a new Chrome window opened, or start it manually using:")
            print("   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=\"/Users/hariommishra/Desktop/dev/ai/ai-job-application-agent/chrome_profile\"\n")
            return {"all_jobs": []}

    with sync_playwright() as p:
        print(f"Connecting to your running Chrome profile over CDP ({CDP_URL})...")
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]

        # Reuse existing LinkedIn tab if open
        page = None
        is_new_page = False
        for tab in context.pages:
            if "linkedin" in tab.url:
                page = tab
                print("Found an already active LinkedIn tab — attaching to it.")
                break

        if not page:
            page = context.new_page()
            is_new_page = True
            print("Opened a new tab.")

        try:
            cards = scrape_job_listings(page, role, location)
        except Exception as e:
            print(f"LinkedIn scraping failed: {e}")
            if is_new_page:
                page.close()
            return {"all_jobs": []}

        if not cards:
            if is_new_page:
                page.close()
            return {"all_jobs": []}

        for card in cards:
            description = scrape_job_description(page, card["url"]) if card.get("url") else ""

            try:
                job = extract_job_fields(
                    job_id=card["id"],
                    title=card["title"],
                    company_name=card["company_name"],
                    location=card["location"],
                    description=description,
                )
                job.url = card.get("url")
            except Exception as e:
                print(f"LLM extraction failed for job {card['id']}: {e}")
                job = Job(
                    id=card["id"],
                    title=card["title"],
                    company_name=card["company_name"],
                    location=card["location"],
                    job_description=description,
                    url=card.get("url")
                )

            jobs.append(job)
            print(f"  fetched: {job.title} @ {job.company_name}")

        if is_new_page:
            page.close()

    print(f"fetched {len(jobs)} jobs from LinkedIn.")
    return {"all_jobs": jobs}
