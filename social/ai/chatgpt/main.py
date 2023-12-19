import os
from openai import OpenAI
from typing import Optional


def query_openai(query: str, model: str = "gpt-3.5-turbo") -> Optional[str]:
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
        organization=os.environ.get("OPENAI_ORG_ID"),
    )
    result = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": query,
            }
        ],
        model=model,
    )
    if result.choices[0].finish_reason != "stop":
        return None
    return result.choices[0].message.content


def get_cover_letter(profile_info: str, job_info: str) -> str:
    question = "Hey, can you write a cover letter for me?"
    query = f"{question}\n\n{profile_info}\n\n{job_info}"
    return query_openai(query)
