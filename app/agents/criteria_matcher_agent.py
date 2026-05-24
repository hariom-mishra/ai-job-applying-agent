"""will iterate through job list match criteria and add the matching
one to the filtered jobs"""
from app.models.state import JobApplicationState

def criteria_matcher_agent(state: JobApplicationState):
    print(" matching criteria...")
    filtered_jobs = []
    for job in state.all_jobs:
        if all(skill in state.profile.skills for skill in job.skills) and job.experience_required == state.profile.experience:
            filtered_jobs.append(job)
    return {"filtered_jobs": filtered_jobs}