from pydantic import BaseModel

class Job(BaseModel):
    title: str
    company_name: str
    job_description: str
    location: str
    skills: list
    experience_required: str
    responsibilities: str
    