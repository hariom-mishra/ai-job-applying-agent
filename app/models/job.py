from pydantic import BaseModel
from typing import Optional, List

class Job(BaseModel):
    id: str
    title: Optional[str] = None
    company_name: Optional[str] = None
    job_description: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = []
    experience_required: Optional[str] = None
    responsibilities: Optional[str] = None
    salery: Optional[str] = None
    job_type: Optional[str] = None
    url: Optional[str] = None
    