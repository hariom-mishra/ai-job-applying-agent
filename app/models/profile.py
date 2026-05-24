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

    @property
    def skills(self) -> list:
        return self.key_skills

    @property
    def experience(self) -> str:
        if self.experiences and isinstance(self.experiences, list):
            first_exp = self.experiences[0]
            if isinstance(first_exp, dict):
                return first_exp.get("duration", "")
        return ""
