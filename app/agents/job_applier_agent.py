"""
Automates LinkedIn Easy Apply applications by connecting to the user's logged-in Chrome session via CDP.
"""
import re
import urllib.request
from urllib.parse import quote
from playwright.sync_api import sync_playwright
from app.models.state import JobApplicationState

CDP_URL = "http://localhost:9222"


def _is_cdp_running() -> bool:
    try:
        urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=1)
        return True
    except Exception:
        return False


def _extract_job_id(url: str) -> str | None:
    match = re.search(r"/jobs/view/(\d+)", url)
    return match.group(1) if match else None


def _fill_easy_apply_form(page, profile):
    try:
        # 1. Text Fields & Textareas
        inputs = page.query_selector_all(
            "input[type='text'], input[type='tel'], input[type='email'], input[type='number'], textarea"
        )
        for inp in inputs:
            try:
                if inp.input_value():
                    continue
            except Exception:
                continue

            label_text = ""
            inp_id = inp.get_attribute("id")
            if inp_id:
                label_el = page.query_selector(f"label[for='{inp_id}']")
                if label_el:
                    label_text = label_el.inner_text().lower()

            if not label_text:
                placeholder = inp.get_attribute("placeholder") or ""
                label_text = placeholder.lower()

            input_type = inp.get_attribute("type") or "text"
            is_number = input_type == "number"

            if "phone" in label_text or "mobile" in label_text or "tel" in label_text:
                inp.fill(profile.phone)
            elif "email" in label_text:
                inp.fill(profile.email)
            elif "experience" in label_text or "years" in label_text:
                inp.fill("2")
            elif "gpa" in label_text:
                inp.fill("3.8")
            elif "salary" in label_text or "expectation" in label_text or "compensation" in label_text:
                inp.fill("120000")
            elif is_number:
                inp.fill("3")
            else:
                inp.fill("Yes")

        # 2. Select dropdowns
        selects = page.query_selector_all("select")
        for sel in selects:
            try:
                current = sel.evaluate("el => el.value")
                if current:
                    continue
                options = sel.query_selector_all("option")
                for opt in options:
                    val = opt.get_attribute("value") or ""
                    if val.strip() and val.strip() not in ("", "Select an option", "Please select"):
                        sel.select_option(value=val)
                        break
            except Exception:
                continue

        # 3. Radio Groups
        radio_groups = page.query_selector_all(".fb-radio, [role='radiogroup']")
        for group in radio_groups:
            try:
                checked = group.query_selector("input:checked")
                if checked:
                    continue
                group_text = group.inner_text().lower()
                yes_opt = group.query_selector("label:has-text('Yes')") or group.query_selector("label:has-text('yes')")
                no_opt = group.query_selector("label:has-text('No')") or group.query_selector("label:has-text('no')")
                if "sponsorship" in group_text or "sponsor" in group_text or "visa" in group_text:
                    if no_opt:
                        page.evaluate("el => el.click()", no_opt)
                elif "authorized" in group_text or "legally" in group_text or "right to work" in group_text:
                    if yes_opt:
                        page.evaluate("el => el.click()", yes_opt)
                else:
                    if yes_opt:
                        page.evaluate("el => el.click()", yes_opt)
                    elif no_opt:
                        page.evaluate("el => el.click()", no_opt)
            except Exception:
                continue

        # 4. Checkboxes
        checkboxes = page.query_selector_all("input[type='checkbox']")
        for cb in checkboxes:
            try:
                is_checked = page.evaluate("el => el.checked", cb)
                if not is_checked:
                    page.evaluate(
                        "el => { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })); }", cb
                    )
            except Exception:
                continue

    except Exception as e:
        print(f"Error while filling form fields: {e}")


def job_applier_agent(state: JobApplicationState):
    print("\n🚀 Job applier agent running...")

    processed_jobs = list(state.processed_jobs)
    applied_jobs = list(state.applied_jobs)

    current_job = state.all_jobs[len(processed_jobs)]
    print(f"Evaluating job: {current_job.title} @ {current_job.company_name}")

    is_eligible = any(job.id == current_job.id for job in state.filtered_jobs)
    if not is_eligible:
        print("❌ Job did not match eligibility criteria. Skipping.")
        processed_jobs.append(current_job)
        return {"processed_jobs": processed_jobs, "applied_jobs": applied_jobs}

    if not _is_cdp_running():
        print("⚠️ CDP is not active. Start Chrome with --remote-debugging-port=9222")
        processed_jobs.append(current_job)
        return {"processed_jobs": processed_jobs, "applied_jobs": applied_jobs}

    job_url = current_job.url or ""
    if not job_url:
        print("❌ No URL for this job. Skipping.")
        processed_jobs.append(current_job)
        return {"processed_jobs": processed_jobs, "applied_jobs": applied_jobs}

    # Extract numeric job ID so we can use the search-panel URL where the Apply button actually lives
    job_id = _extract_job_id(job_url)
    if not job_id:
        print(f"❌ Could not extract job ID from URL: {job_url}. Skipping.")
        processed_jobs.append(current_job)
        return {"processed_jobs": processed_jobs, "applied_jobs": applied_jobs}

    print("✅ Job is eligible. Initiating automated application...")

    with sync_playwright() as p:
        try:
            print(f"Connecting to Chrome over CDP ({CDP_URL})...")
            browser = p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]
            page = context.new_page()

            # LinkedIn's Apply button only appears on the search-results page (right panel),
            # NOT on the direct /jobs/view/ URL. Navigate using currentJobId param.
            role = quote(state.profile.looking_for)
            location = quote(state.profile.location)
            panel_url = (
                f"https://www.linkedin.com/jobs/search/"
                f"?currentJobId={job_id}&f_AL=true&keywords={role}&location={location}"
            )
            print(f"Opening job in search panel: {panel_url}")
            page.goto(panel_url, wait_until="domcontentloaded")

            # Wait for the LinkedIn Apply button (class jobs-apply-button)
            print("Waiting for LinkedIn Apply button...")
            try:
                page.wait_for_selector(".jobs-apply-button", timeout=12000)
            except Exception:
                print("❌ Apply button did not appear — job may not support LinkedIn Easy Apply. Skipping.")
                page.close()
                processed_jobs.append(current_job)
                return {"processed_jobs": processed_jobs, "applied_jobs": applied_jobs}

            # Click the primary Apply button (the one with aria-label "LinkedIn Apply to ...")
            # There can be multiple; click the one with the highest artdeco size (most prominent)
            clicked = page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('button.jobs-apply-button'));
                // Prefer the larger button (artdeco-button--3 > artdeco-button--2)
                const btn = btns.find(el => el.className.includes('artdeco-button--3') && el.offsetWidth > 0) ||
                            btns.find(el => el.offsetWidth > 0);
                if (btn) { btn.click(); return btn.getAttribute('aria-label') || 'clicked'; }
                return null;
            }""")

            if not clicked:
                print("❌ Could not click the Apply button. Skipping.")
                page.close()
                processed_jobs.append(current_job)
                return {"processed_jobs": processed_jobs, "applied_jobs": applied_jobs}

            print(f"✅ Clicked Apply button: {clicked}")

            # Wait for the Easy Apply modal
            try:
                print("Waiting for Easy Apply modal...")
                page.wait_for_selector(
                    ".jobs-easy-apply-modal, .artdeco-modal__content, [role='dialog']",
                    timeout=10000
                )
                print("Modal opened.")
            except Exception as e:
                print(f"❌ Easy Apply modal did not open: {e}")
                page.close()
                processed_jobs.append(current_job)
                return {"processed_jobs": processed_jobs, "applied_jobs": applied_jobs}

            # Multi-step form loop
            prev_step_text = ""
            for step in range(15):
                print(f"\n--- Step {step + 1} ---")
                page.wait_for_timeout(1500)

                _fill_easy_apply_form(page, state.profile)
                page.wait_for_timeout(800)

                # Detect current step heading to track progress
                step_heading = page.evaluate("""() => {
                    const modal = document.querySelector('.artdeco-modal__content, [role="dialog"]');
                    if (!modal) return '';
                    const h = modal.querySelector('h3, h2, .jobs-easy-apply-modal__heading, [class*="header"]');
                    return h ? h.textContent.trim() : '';
                }""")
                print(f"Step heading: {step_heading!r}")

                # Find and click the primary action button
                button_action = page.evaluate("""() => {
                    const modal = document.querySelector('.artdeco-modal__content, [role="dialog"], .jobs-easy-apply-modal');
                    if (!modal) return null;
                    const primaryBtns = Array.from(modal.querySelectorAll('button.artdeco-button--primary'));
                    const btn = primaryBtns.find(el => el.offsetWidth > 0 && el.offsetHeight > 0);
                    if (!btn) return null;
                    const text = (btn.textContent || '').trim().toLowerCase();
                    const aria = (btn.getAttribute('aria-label') || '').trim().toLowerCase();
                    btn.click();
                    if (text.includes('submit') || aria.includes('submit')) return 'submit';
                    if (text.includes('review') || aria.includes('review')) return 'review';
                    return 'next';
                }""")

                print(f"Button action: {button_action}")

                if button_action == "submit":
                    page.wait_for_timeout(3000)
                    # Dismiss the confirmation modal if present
                    try:
                        page.wait_for_selector(".artdeco-modal button", timeout=4000)
                        page.evaluate("""() => {
                            const btns = Array.from(document.querySelectorAll('.artdeco-modal button'));
                            const done = btns.find(b => /done|close|dismiss/i.test(b.textContent));
                            if (done) done.click();
                        }""")
                    except Exception:
                        pass
                    applied_jobs.append(current_job.id)
                    print(f"🎉 Applied to {current_job.title} @ {current_job.company_name}!")
                    break
                elif button_action in ("next", "review"):
                    page.wait_for_timeout(2000)
                    # Detect if we're stuck (same step text, no progress)
                    if step_heading and step_heading == prev_step_text:
                        print("⚠️  Step did not advance — form may have unfilled required fields. Stopping.")
                        break
                    prev_step_text = step_heading
                else:
                    print("No primary button found in modal — stopping.")
                    break

            page.close()

        except Exception as e:
            print(f"Error during application automation: {e}")
            try:
                page.close()
            except Exception:
                pass

    processed_jobs.append(current_job)
    return {"processed_jobs": processed_jobs, "applied_jobs": applied_jobs}
