from groq import Groq, omit

from app.core.config import settings

_client = Groq(api_key=settings.groq_api_key)


def generate(
    prompt: str,
    system_instruction: str | None = None,
    json_mode: bool = False,
) -> str:
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    response = _client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        response_format={"type": "json_object"} if json_mode else omit,
    )
    return response.choices[0].message.content
