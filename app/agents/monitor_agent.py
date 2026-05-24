"""monitors if all the job is process or job list is empty if yest then exit otherwise route to filter agent"""
from app.models.state import JobApplicationState

def monitor_agent(state: JobApplicationState) -> str:
    print("monitor agent running...")
    if len(state.processed_jobs) >= len(state.all_jobs): 
        return "done"
    else:
        return "continue"

    