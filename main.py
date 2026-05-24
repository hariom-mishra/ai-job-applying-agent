from app.graph import job_graph
from app.models.state import JobApplicationState
from app.models.profile import Profile

def main():
    job_graph.invoke(
        JobApplicationState(
            profile=Profile(
                name="Hariom Mishra",
                email="mhariom014@gmail.com",
                phone="1234567890",
                role="AI Engineer",
                key_skills=["Python","FastAPI", "Langgraph","Langchain","RAG","Agentic AI","LLMs"],
                experiences=[
                    {
                        "company": "Junkies Coders",
                        "role": "Software Engineer",
                        "duration": "6 months",
                        "description": "Working on mobile apps"
                    },
                    {
                    "company": "Zulu Club",
                    "role": "Software Engineer",
                    "duration": "2 years",
                    "description": "Working on Mobile Apps and  AI projects"
                }],
                education=[{
                    "degree": "Master of Computer Application",
                    "field": "Computer Science",
                    "year": 2023
                },
                {
                    "degree": "Bachelor of Computer Application",
                    "field": "Computer Science",
                    "year": 2020
                },
                ],
                projects=[
                    {
                        "name": "LinkedIn Job Application Agent",
                        "description": "AI Agent for LinkedIn Job Application"
                    },
                    {
                        "name": "Project 2",
                        "description": "Description 2"
                    }
                ],
                looking_for="Software Engineer",
                location="San Francisco, CA"
            ),
            all_jobs=[],
            processed_jobs=[],
            applied_jobs=[],
            resume="Resume text"
        )
    )
    


if __name__ == "__main__":
    main()
