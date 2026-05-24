"""this agent will fetch jobs for the provided app by opening 
the url on browser and fetch dom collect list of jobs and update the state"""
from app.models.state import JobApplicationState
from app.models.job import Job

def job_fetcher_agent(state: JobApplicationState):
    print(" job fetcher agent running...")
    return {"all_jobs": [
        Job(
            id="1",
            title="Software Engineer",
            company_name="Google",
            job_description="Software Engineer",
            location="Gurugram",
            skills=["Python", "Java", "SQL"],
            experience_required="2-3 years",
            responsibilities="Software Engineer",
            salery="10-15 LPA",
            job_type="Full-time"
        ),
        Job(
            id="2",
            title="Software Engineer",
            company_name="Microsoft",
            job_description="Software Engineer",
            location="Gurugram",
            skills=["Python", "Java", "SQL"],
            experience_required="2-3 years",
            responsibilities="Software Engineer",
            salery="10-15 LPA",
            job_type="Full-time"
        ),
        Job(
            id="3",
            title="Software Engineer",
            company_name="Microsoft",
            job_description="Software Engineer",
            location="Gurugram",
            skills=["Python", "Java", "SQL"],
            experience_required="2-3 years",
            responsibilities="Software Engineer",
            salery="10-15 LPA",
            job_type="Full-time"
        ),
    ]}
