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

    with sync_playwright() as p:
        if _is_cdp_running():
            print(f"Connecting to your running Chrome profile over CDP ({CDP_URL})...")
            browser = p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]

            # Reuse existing LinkedIn tab if open
            page = None
            for tab in context.pages:
                if "linkedin" in tab.url:
                    page = tab
                    print("Found an already active LinkedIn tab — attaching to it.")
                    break

            if not page:
                page = context.new_page()
                print("Opened a new tab.")
        else:
            print("CDP not active — launching a headful Playwright browser to run the scraper...")
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            print("Opened a new headful browser.")

        try:
            cards = scrape_job_listings(page, role, location)
        except Exception as e:
            print(f"LinkedIn scraping failed: {e}")
            page.close()
            return {"all_jobs": []}

        if not cards:
            print("No job cards found — LinkedIn may have shown a login wall.")
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
            except Exception as e:
                print(f"LLM extraction failed for job {card['id']}: {e}")
                job = Job(
                    id=card["id"],
                    title=card["title"],
                    company_name=card["company_name"],
                    location=card["location"],
                    job_description=description,
                )

            jobs.append(job)
            print(f"  fetched: {job.title} @ {job.company_name}")

        page.close()

    print(f"fetched {len(jobs)} jobs from LinkedIn.")
    return {"all_jobs": jobs}
