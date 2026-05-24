import re
import time
from typing import Any, Dict, List
from urllib.parse import quote

# BeautifulSoup is an HTML parsing library.
# After the browser loads a page, we get its raw HTML as a string.
# BeautifulSoup converts that string into a tree of objects we can search
# through using CSS selectors — exactly like how browser DevTools let you
# inspect elements by class name or tag.
from bs4 import BeautifulSoup

# Playwright controls a real browser (Chromium, Firefox, or WebKit) from Python.
# `Page` is the type hint for a single browser tab that Playwright gives us.
from playwright.sync_api import Page


def build_search_url(role: str, location: str) -> str:
    # `quote()` URL-encodes special characters so spaces become %20, etc.
    # Without this, a role like "Software Engineer" would break the URL.
    return (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={quote(role)}&location={quote(location)}"
    )


def _text(el) -> str | None:
    return el.get_text(strip=True) if el else None


def _first(*els):
    # Returns the first non-None element from the list — used to try
    # multiple selectors and take whichever one matched.
    return next((el for el in els if el is not None), None)


def _job_id_from_urn(urn: str, fallback: str) -> str:
    match = re.search(r"\d+$", urn)
    return match.group() if match else fallback


def _job_id_from_url(url: str) -> str | None:
    # Logged-in LinkedIn job URLs look like /jobs/view/1234567890/
    # We extract the numeric ID from the path.
    match = re.search(r"/jobs/view/(\d+)", url)
    return match.group(1) if match else None


def scrape_job_listings(
    page: Page, role: str, location: str, max_jobs: int = 10
) -> List[Dict[str, Any]]:
    url = build_search_url(role, location)

    # Navigate to the LinkedIn jobs search URL.
    page.goto(url, wait_until="domcontentloaded", timeout=30000)

    # LinkedIn renders job cards dynamically with JavaScript.
    # Wait for either the logged-in card selector or the public page selector —
    # whichever appears first tells us which version of the page we have.
    page.wait_for_selector(
        # logged-in page selectors
        ".jobs-search-results__list-item, .job-card-container,"
        # public (logged-out) page selectors as fallback
        ".base-search-card, .jobs-search__results-list",
        timeout=15000,
    )

    # Scroll down to trigger lazy-loaded cards.
    for _ in range(3):
        page.evaluate("window.scrollBy(0, 900)")
        time.sleep(1.2)

    soup = BeautifulSoup(page.content(), "html.parser")

    # Try logged-in selectors first, then fall back to public page selectors.
    cards = soup.select("li.jobs-search-results__list-item")[:max_jobs]
    if not cards:
        cards = soup.select(".job-search-card")[:max_jobs]

    results = []
    for i, card in enumerate(cards):

        # --- Job ID ---
        # Logged-in: the <li> carries data-entity-urn="urn:li:jobPosting:XXXXX"
        # or the inner anchor href contains /jobs/view/XXXXX/
        urn = card.get("data-entity-urn", "")
        link_el = _first(
            # logged-in selectors
            card.select_one("a.job-card-list__title--link"),
            card.select_one("a.job-card-container__link"),
            # public page fallback
            card.select_one("a.base-card__full-link"),
        )
        href = link_el["href"] if link_el and link_el.get("href") else None
        job_id = (
            _job_id_from_urn(urn, fallback="")
            or (href and _job_id_from_url(href))
            or str(i + 1)
        )

        # --- Title ---
        title_el = _first(
            # logged-in: title is inside the anchor, sometimes wrapped in <strong>
            card.select_one("a.job-card-list__title--link strong"),
            card.select_one("a.job-card-list__title--link"),
            card.select_one(".job-card-list__title"),
            # public page fallback
            card.select_one(".base-search-card__title"),
        )

        # --- Company ---
        company_el = _first(
            # logged-in
            card.select_one(".job-card-container__primary-description"),
            card.select_one(".artdeco-entity-lockup__subtitle span"),
            # public page fallback
            card.select_one(".base-search-card__subtitle"),
        )

        # --- Location ---
        loc_el = _first(
            # logged-in
            card.select_one(".job-card-container__metadata-item"),
            card.select_one(".artdeco-entity-lockup__caption span"),
            # public page fallback
            card.select_one(".job-search-card__location"),
        )

        results.append({
            "id": job_id,
            "title": _text(title_el),
            "company_name": _text(company_el),
            "location": _text(loc_el),
            "url": href,
        })

    return results


def scrape_job_description(page: Page, job_url: str) -> str:
    try:
        page.goto(job_url, wait_until="domcontentloaded", timeout=20000)

        # Wait for the description container — different class on logged-in vs public page.
        page.wait_for_selector(
            # logged-in
            ".jobs-description-content__text,"
            ".jobs-description__content,"
            # public page fallback
            ".show-more-less-html__markup,"
            ".description__text",
            timeout=10000,
        )

        soup = BeautifulSoup(page.content(), "html.parser")

        desc_el = _first(
            # logged-in selectors
            soup.select_one(".jobs-description-content__text"),
            soup.select_one(".jobs-description__content"),
            # public page fallback
            soup.select_one(".show-more-less-html__markup"),
            soup.select_one(".description__text"),
        )

        return desc_el.get_text(separator="\n", strip=True) if desc_el else ""
    except Exception:
        return ""
