from typing import Literal
from pydantic import BaseModel
from app.models.profile import Profile
from app.models.job import Job
from typing import List

class JobApplicationState(BaseModel):
    all_jobs: List[Job]
    filtered_jobs: List[Job]
    profile: Profile
    applied_jobs: List[str]
    resume: str