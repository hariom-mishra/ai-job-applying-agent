from app.graph import job_graph
from app.models.state import JobApplicationState
from app.models.profile import Profile

def main():
    job_graph.invoke(
        JobApplicationState(
            profile=Profile(
                name="John Doe",
                email="[EMAIL_ADDRESS]",
                phone="1234567890",
                role="Software Engineer",
                key_skills=["Python", "Java", "SQL"],
                experiences=[{
                    "company": "Google",
                    "role": "Software Engineer",
                    "duration": "2 years",
                    "description": "Working on AI projects"
                }],
                education=[{
                    "degree": "Bachelor of Science",
                    "field": "Computer Science",
                    "year": 2022
                }],
                projects=[
                    {
                        "name": "Project 1",
                        "description": "Description 1"
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
            filtered_jobs=[],
            applied_jobs=[],
            resume="Resume text"
        )
    )
    


if __name__ == "__main__":
    main()
