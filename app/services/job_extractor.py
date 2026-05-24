from langchain_core.prompts import ChatPromptTemplate

from app.lllm import llm
from app.models.job import Job

_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Populate the Job object using the provided fields. "
        "Extract skills, experience_required, responsibilities, salery, and job_type "
        "from the description. Keep id, title, company_name, location, and "
        "job_description exactly as given.",
    ),
    (
        "human",
        "id: {id}\n"
        "title: {title}\n"
        "company_name: {company_name}\n"
        "location: {location}\n"
        "job_description: {job_description}",
    ),
])

_extractor = _prompt | llm.with_structured_output(Job)


def extract_job_fields(
    job_id: str,
    title: str | None,
    company_name: str | None,
    location: str | None,
    description: str,
) -> Job:
    return _extractor.invoke({
        "id": job_id,
        "title": title or "",
        "company_name": company_name or "",
        "location": location or "",
        "job_description": description,
    })
