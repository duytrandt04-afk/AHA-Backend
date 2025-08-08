import io
from pydub import AudioSegment
from pydub.playback import play
from app.models.llm_gateway import client
from app.api.database.redis_client import get_config

# Most reliable approach with proper error handling
def generate_audio(text: str):
    """Most robust approach with comprehensive error handling"""
    try:
        
        # Use non-streaming for reliability
        response = client.audio.speech.create(
            model=get_config("tts_config").get("model"),
            voice=get_config("tts_config").get("voice"),
            input=text,
            instructions=get_config("tts_config").get("instructions"),
        )
        
        # Validate response thoroughly
        if not hasattr(response, 'content') or not response.content:
            raise ValueError("No audio content received from API")
        
        content_size = len(response.content)
        
        if content_size < 100:  # Minimum viable MP3 size
            raise ValueError(f"Audio data too small: {content_size} bytes")
        
        # Create audio segment and play
        audio_data = io.BytesIO(response.content)
        try:
            audio_segment = AudioSegment.from_file(audio_data, format="mp3")
        except Exception as decode_error:
            print(f"MP3 decode error: {decode_error}")
            # Save problematic file for debugging
            with open("debug_failed_audio.mp3", "wb") as f:
                f.write(response.content)
            raise ValueError(f"Failed to decode MP3: {decode_error}")
        
        # Play the audio
        play(audio_segment)
        
    except Exception as e:
        raise