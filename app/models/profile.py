from pydantic import BaseModel

class Profile(BaseModel):
    name: str
    email: str
    phone: str
    role: str
    key_skills: list
    experiences: list
    education: list
    projects: list    
    looking_for: str
    location: str
