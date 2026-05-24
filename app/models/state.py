from typing import Literal
from pydantic import BaseModel, Field
from app.models.profile import Profile
from app.models.job import Job
from typing import List

class JobApplicationState(BaseModel):
    all_jobs: List[Job] = Field(default_factory=list)
    processed_jobs: List[Job] = Field(default_factory=list)
    profile: Profile
    applied_jobs: List[str] = Field(default_factory=list)
    resume: str = ""
