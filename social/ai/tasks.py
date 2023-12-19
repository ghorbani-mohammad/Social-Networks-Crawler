from ai.chatgpt.main import query_openai


def get_cover_letter(profile_info: str, job_info: str) -> str:
    question = "Hey, can you write a cover letter for me?"
    query = f"{question}\n\n{profile_info}\n\n{job_info}"
    return query_openai(query)
