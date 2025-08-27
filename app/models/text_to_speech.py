from app.models.llm_gateway import client
from app.api.database.redis_client import get_config

def generate_audio(text: str):
    """Stream audio chunks from the API directly."""
    response = client.audio.speech.create(
        model=get_config("tts_config")["model"],
        voice=get_config("tts_config")["voice"],
        input=text,
        instructions=get_config("tts_config")["instructions"],
    )

    if not hasattr(response, "iter_bytes"):
        # If your API client doesn't support streaming, fallback to whole content
        yield response.content
        return

    # If streaming is supported:
    for chunk in response.iter_bytes():
        if chunk:
            yield chunk