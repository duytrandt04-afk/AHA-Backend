import pyaudio
from .audio_settings import get_optimized_settings
from app.api.database.redis_client import get_config

class Config:
    def __init__(self):
        self.api_key = get_config("api_keys").get("OPENAI_API_KEY")
        self.ws_url = get_config("api_keys").get("REALTIME_API")
        
        # Load optimized settings
        settings = get_optimized_settings()
        
        # Audio settings
        self.chunk_size = settings['chunk_size']
        self.rate = settings['rate']
        self.format = pyaudio.paInt16  # Correct PyAudio format
        
        # Timing settings
        self.reengage_delay_ms = settings['reengage_delay']
        
        # Audio enhancement settings
        self.mic_gain_multiplier = settings['mic_gain']
        self.min_audio_level = settings['min_level']
        
        # Speech detection settings (for OpenAI session config)
        self.speech_threshold = settings['speech_threshold']
        self.silence_duration_ms = settings['silence_duration']
        self.prefix_padding_ms = settings['prefix_padding']