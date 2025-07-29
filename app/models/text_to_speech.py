from app.models.llm_gateway import client
from app.api.database.redis_client import get_config

def generate_audio(text: str):
    with client.audio.speech.with_streaming_response.create(
            model=get_config("tts_config").get("model"),
            voice=get_config("tts_config").get("voice"),
            input=text,
            instructions=get_config("tts_config").get("instructions"),
        ) as response:
            for chunk in response.iter_bytes():
                yield chunk