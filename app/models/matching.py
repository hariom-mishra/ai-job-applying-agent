from pydantic import BaseModel

class Matching(BaseModel):
    match_score: str
    eligible: str
    reason: str
