"""will iterate through job list match criteria and add the matching
one to the filtered jobs"""
from app.models.state import JobApplicationState
from app.llm import llm
from langchain_core.prompts import ChatPromptTemplate
import json
from app.models.matching import Matching

def criteria_matcher_agent(state: JobApplicationState):
    print(" matching criteria...")
    
    system_prompt = """You are a job criteria matching agent. 
    You will be given a job and a profile and you have to match 
    the job with the profile."""
    prompt = """
    Job Details: {job_description}

    Profile Details:
    - Skills: {skills}
    - Experience: {experience}

    Based on the profile details, evaluate whether the candidate is a good fit for this job.
    
    Answer Format:
    - generate json format as 
        {{ 
            "match_score": "score", 
            "eligible": "Yes/No", 
            "reason": "Brief explanation" 
        }} 
    """
    llm_with_structured_output = llm.with_structured_output(Matching)
    
    
    filtered_jobs = []
    for job in state.all_jobs:
        response = llm_with_structured_output.invoke(
            ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", prompt)
            ]).format_messages(
                job_description=job.job_description or f"Software Engineering / Developer position with title: '{job.title}'. Since the detailed description failed to load, please evaluate eligibility based on this job title and your knowledge of software engineering roles.",
                skills=", ".join(state.profile.key_skills),
                experience=str(state.profile.experiences)
            )
        )
        print(f"  🔍 LLM Eval: {job.title} @ {job.company_name} -> Eligible: {response.eligible} | Reason: {response.reason}")
        if response.eligible == "Yes":
            filtered_jobs.append(job)
    return {"filtered_jobs": filtered_jobs}