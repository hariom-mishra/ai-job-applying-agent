# AI Job Application Agent

An autonomous multi-agent system that automates LinkedIn job applications end-to-end — from scraping listings and evaluating fit with an LLM, to filling and submitting Easy Apply forms via browser automation.

---

## Overview

This project implements a **LangGraph-orchestrated agentic workflow** with four specialized agents working together:

1. **Job Fetcher** — Scrapes LinkedIn job listings and extracts structured fields using an LLM
2. **Criteria Matcher** — Evaluates each job against the candidate's profile using GPT-4o-mini
3. **Job Applier** — Navigates LinkedIn, fills multi-step Easy Apply forms, and submits applications
4. **Monitor** — Routes the workflow back to continue or terminates when all jobs are processed

The system connects to a live Chrome browser session via the Chrome DevTools Protocol (CDP), which means it uses your existing LinkedIn login — no credential handling required.

---

## Architecture

```
START
  └─► Job Fetcher Agent
        └─► Monitor Agent ──(done)──► END
              └─(continue)─► Criteria Matcher Agent
                                  └─► Job Applier Agent
                                        └─► Monitor Agent
                                              ├─(done)──► END
                                              └─(continue)─► Job Applier Agent
```

### Agent Responsibilities

| Agent | File | Responsibility |
|---|---|---|
| Job Fetcher | `app/agents/job_fetcher_agent.py` | Scrapes LinkedIn job cards and job descriptions, extracts structured data via LLM |
| Criteria Matcher | `app/agents/criteria_matcher_agent.py` | Scores and filters jobs by candidate eligibility using LLM-structured output |
| Job Applier | `app/agents/job_applier_agent.py` | Drives the browser to click Apply, fill form fields, navigate steps, and submit |
| Monitor | `app/agents/monitor_agent.py` | Checks processing progress and routes the graph |

### Shared State

All agents read and write a single `JobApplicationState` object passed through the graph:

```python
class JobApplicationState(TypedDict):
    all_jobs: List[Job]          # fetched from LinkedIn
    filtered_jobs: List[Job]     # passed criteria check
    processed_jobs: List[Job]    # evaluated (eligible or not)
    applied_jobs: List[str]      # job IDs successfully submitted
    profile: Profile             # candidate profile
    resume: str                  # candidate resume text
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM | OpenAI `gpt-4o-mini` via LangChain |
| Browser automation | [Playwright](https://playwright.dev/) (CDP mode) |
| HTML parsing | BeautifulSoup 4 |
| Data validation | Pydantic v2 |
| Package management | [uv](https://github.com/astral-sh/uv) |
| Python | 3.14 |

---

## Prerequisites

- **Python 3.14+**
- **uv** package manager — `pip install uv`
- **Google Chrome** installed at the default macOS path
- **LinkedIn account** (already logged in via the Chrome profile)
- **OpenAI API key**

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-job-application-agent.git
cd ai-job-application-agent
```

### 2. Install dependencies

```bash
uv sync
```

Or with pip:

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-proj-your-key-here
```

### 4. Launch Chrome with CDP enabled

The agent connects to a running Chrome instance rather than spawning a headless browser. This lets it reuse your existing LinkedIn session.

```bash
open -a "Google Chrome" --args \
  --remote-debugging-port=9222 \
  --user-data-dir="$(pwd)/chrome_profile"
```

Verify CDP is active:

```bash
curl -s http://localhost:9222/json/version
```

Log in to LinkedIn in this browser window before running the agent.

---

## Usage

Edit `main.py` to set your candidate profile:

```python
profile = Profile(
    name="Your Name",
    email="you@example.com",
    phone="1234567890",
    role="AI Engineer",
    key_skills=["Python", "LangChain", "LangGraph", "RAG", "LLMs"],
    experiences=[
        {
            "company": "Acme Corp",
            "role": "ML Engineer",
            "duration": "2 years",
            "description": "Built RAG pipelines and LLM-powered APIs"
        }
    ],
    education=[{"degree": "MCA", "field": "Computer Science", "year": "2023"}],
    projects=[{"name": "...", "description": "..."}],
    looking_for="AI Engineer",
    location="San Francisco, CA"
)
```

Run the agent:

```bash
uv run python main.py
# or
python main.py
```

The agent will:
1. Search LinkedIn for Easy Apply jobs matching your role and location
2. Evaluate each job against your profile using the LLM
3. Auto-apply to eligible jobs
4. Print a summary of applied job IDs

---

## Project Structure

```
ai-job-application-agent/
├── app/
│   ├── graph.py                      # LangGraph workflow definition
│   ├── llm.py                        # OpenAI LLM initialization
│   ├── agents/
│   │   ├── job_fetcher_agent.py      # LinkedIn scraping + LLM extraction
│   │   ├── criteria_matcher_agent.py # LLM-based eligibility scoring
│   │   ├── job_applier_agent.py      # Browser form automation
│   │   └── monitor_agent.py          # Workflow router
│   ├── models/
│   │   ├── state.py                  # Shared LangGraph state
│   │   ├── job.py                    # Job data model
│   │   ├── profile.py                # Candidate profile model
│   │   └── matching.py              # Eligibility result model
│   └── services/
│       ├── linkedin_scraper.py       # Playwright + BeautifulSoup scraping
│       └── job_extractor.py          # LLM-based field extraction
├── main.py                           # Entry point
├── pyproject.toml
├── requirements.txt
└── .env                              # API keys (not committed)
```

---

## How the Form Filler Works

The Job Applier agent handles LinkedIn's multi-step Easy Apply modal autonomously:

- Detects field labels (phone, email, years of experience, GPA, salary expectations)
- Fills text inputs using profile values or intelligent defaults
- Handles dropdowns, radio buttons, and checkboxes
- Answers common screening questions (visa sponsorship → No, right to work → Yes)
- Navigates Next → Review → Submit across up to 15 form steps
- Detects stuck states and skips unresolvable forms

---

## Configuration

Key constants you may want to adjust:

**`app/agents/job_fetcher_agent.py`**

| Constant | Default | Description |
|---|---|---|
| `max_jobs` | `10` | Maximum job listings to fetch per run |
| CDP port | `9222` | Chrome DevTools Protocol port |

**`app/llm.py`**

| Setting | Value |
|---|---|
| Model | `gpt-4o-mini` |
| Temperature | `0.2` |

---

## Limitations

- **LinkedIn ToS** — Automated interactions with LinkedIn may violate their Terms of Service. Use responsibly and at your own risk.
- **Form variability** — Easy Apply forms differ by employer. Novel field types may not be handled automatically.
- **Captchas** — The agent does not handle CAPTCHA or security challenges.
- **Session dependency** — Requires an active LinkedIn session in the connected Chrome instance.
- **macOS only** — The Chrome launch command is macOS-specific; adjust the path for Linux/Windows.

