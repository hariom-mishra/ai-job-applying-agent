"""
this agent will apply for the job provided if it is easy apply
 then apply otherwise if it needs to fill form then fill the form
  to apply the job and then update the state
 """
from app.models.state import JobApplicationState

def job_applier_agent(state: JobApplicationState):
    print(" applying jobs...")
    pass