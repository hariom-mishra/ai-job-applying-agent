"""
Automates LinkedIn Easy Apply applications by connecting to the user's logged-in Chrome session via CDP.
"""
import urllib.request
from playwright.sync_api import sync_playwright
from app.models.state import JobApplicationState

CDP_URL = "http://localhost:9222"


def _is_cdp_running() -> bool:
    try:
        urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=1)
        return True
    except Exception:
        return False


def _fill_easy_apply_form(page, profile):
    try:
        # 1. Text Fields & Textareas
        inputs = page.query_selector_all("input[type='text'], input[type='tel'], input[type='email'], textarea")
        for inp in inputs:
            # Skip if already has value
            if inp.input_value():
                continue

            # Try to find corresponding label text
            label_text = ""
            inp_id = inp.get_attribute("id")
            if inp_id:
                label_el = page.query_selector(f"label[for='{inp_id}']")
                if label_el:
                    label_text = label_el.inner_text().lower()

            if not label_text:
                # Try parent wrapper or placeholder
                placeholder = inp.get_attribute("placeholder")
                if placeholder:
                    label_text = placeholder.lower()

            # Fill based on label
            if "phone" in label_text or "mobile" in label_text or "tel" in label_text:
                inp.fill(profile.phone)
            elif "email" in label_text:
                inp.fill(profile.email)
            elif "experience" in label_text or "years" in label_text:
                inp.fill("2")  # Default to 2 years
            elif "gpa" in label_text:
                inp.fill("3.8")
            elif "salary" in label_text or "expectation" in label_text:
                inp.fill("120000")
            else:
                inp.fill("Yes")  # Friendly fallback for simple verification text fields

        # 2. Radio Groups (Yes/No questions)
        radio_groups = page.query_selector_all(".fb-radio, [role='radiogroup']")
        for group in radio_groups:
            # Check if any input in the group is already checked
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
                # Default to Yes
                if yes_opt:
                    page.evaluate("el => el.click()", yes_opt)
                elif no_opt:
                    page.evaluate("el => el.click()", no_opt)

        # 3. Checkboxes
        checkboxes = page.query_selector_all("input[type='checkbox']")
        for cb in checkboxes:
            is_checked = page.evaluate("el => el.checked", cb)
            if not is_checked:
                page.evaluate("el => { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })); }", cb)
    except Exception as e:
        print(f"Error while filling form fields: {e}")


def job_applier_agent(state: JobApplicationState):
    print("\n🚀 Job applier agent running...")

    processed_jobs = list(state.processed_jobs)
    applied_jobs = list(state.applied_jobs)

    # Grab the current job to process
    currrent_job = state.all_jobs[len(processed_jobs)]
    print(f"Evaluating job: {currrent_job.title} @ {currrent_job.company_name}")

    # Check if the job was filtered/eligible
    is_eligible = any(job.id == currrent_job.id for job in state.filtered_jobs)
    if not is_eligible:
        print("❌ Job did not match eligibility criteria. Skipping application.")
        processed_jobs.append(currrent_job)
        return {"processed_jobs": processed_jobs, "applied_jobs": applied_jobs}

    # Job is eligible - Proceed to apply via CDP
    if not _is_cdp_running():
        print("⚠️ CDP is not active on http://localhost:9222.")
        print("👉 Please start Google Chrome with remote debugging active so the applier agent can control it!")
        processed_jobs.append(currrent_job)
        return {"processed_jobs": processed_jobs, "applied_jobs": applied_jobs}

    print("✅ Job is eligible. Initiating automated application...")
    with sync_playwright() as p:
        try:
            print(f"Connecting to your running Chrome profile over CDP ({CDP_URL})...")
            browser = p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]
            page = context.new_page()

            # Navigate to the job page
            job_url = currrent_job.url
            if job_url:
                if not job_url.startswith("http"):
                    job_url = f"https://www.linkedin.com{job_url}"

                print(f"Opening job page in new tab: {job_url}")
                page.goto(job_url, wait_until="load")
                page.wait_for_timeout(3000)

                # 1. Click Easy Apply button via direct DOM script
                print("Looking for 'Easy Apply' button...")
                page.wait_for_timeout(2000) # Wait for page elements to settle
                
                clicked_easy_apply = page.evaluate("""() => {
                    const elements = Array.from(document.querySelectorAll('button, span, a, div[role="button"]'));
                    const btn = elements.find(el => {
                        const text = el.textContent || '';
                        return text.trim() === 'Easy Apply' && el.offsetWidth > 0 && el.offsetHeight > 0;
                    });
                    if (btn) {
                        btn.click();
                        return true;
                    }
                    return false;
                }""")

                if clicked_easy_apply:
                    print("Found and clicked 'Easy Apply' button successfully!")
                    
                    # Wait for the Easy Apply modal to load
                    try:
                        print("Waiting for Easy Apply modal to load...")
                        page.wait_for_selector(".jobs-easy-apply-modal, [role='dialog'], .artdeco-modal", timeout=8000)
                        print("Easy Apply modal loaded successfully.")
                    except Exception as e:
                        print(f"Easy Apply modal did not appear: {e}")
                        page.close()
                        processed_jobs.append(currrent_job)
                        return {"processed_jobs": processed_jobs, "applied_jobs": applied_jobs}

                    # Multi-step loop to fill forms and click next
                    for step in range(10):
                        # Fill inputs on this step first
                        print(f"Filling out inputs for step {step + 1}...")
                        _fill_easy_apply_form(page, state.profile)
                        page.wait_for_timeout(1000)

                        # Find and click the Next/Review/Submit button via direct DOM script
                        button_action = page.evaluate("""() => {
                            const modal = document.querySelector('.artdeco-modal, [role="dialog"], .jobs-easy-apply-modal');
                            if (!modal) return null;
                            const buttons = Array.from(modal.querySelectorAll('button.artdeco-button--primary'));
                            const primaryBtn = buttons.find(el => el.offsetWidth > 0 && el.offsetHeight > 0);
                            if (primaryBtn) {
                                const text = (primaryBtn.textContent || '').trim().toLowerCase();
                                const aria = (primaryBtn.getAttribute('aria-label') || '').trim().toLowerCase();
                                primaryBtn.click();
                                if (text.includes('submit') || aria.includes('submit')) {
                                    return 'submit';
                                }
                                return 'next';
                            }
                            return null;
                        }""")

                        if button_action == 'submit':
                            print("Submit button clicked! Submitting application...")
                            page.wait_for_timeout(3000)
                            applied_jobs.append(currrent_job.id)
                            print(f"🎉 Successfully applied to {currrent_job.title} @ {currrent_job.company_name}!")
                            break
                        elif button_action == 'next':
                            print("Clicked Next/Review button successfully.")
                            page.wait_for_timeout(2000)
                        else:
                            print("No active primary modal button found. Stopping form flow.")
                            break
                else:
                    print("No 'Easy Apply' button found on this job page (or it requires external application). Skipping automated apply.")
            page.close()
        except Exception as e:
            print(f"Error during job application automation: {e}")

    processed_jobs.append(currrent_job)
    return {"processed_jobs": processed_jobs, "applied_jobs": applied_jobs}
    