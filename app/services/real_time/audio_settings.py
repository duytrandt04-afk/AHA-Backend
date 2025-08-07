# Microphone settings
MIC_GAIN_MULTIPLIER = 3.0  # Increase this to boost microphone input (1.0 = no boost, 2.0 = double, etc.)
MIN_AUDIO_LEVEL = 200      # Minimum expected audio level for good quality

# Audio detection settings
SPEECH_DETECTION_THRESHOLD = 0.3  # Lower = more sensitive to speech (0.1-0.9)
SILENCE_DURATION_MS = 700         # How long to wait before considering speech finished
PREFIX_PADDING_MS = 500           # Audio to include before speech starts

# Audio quality settings
AUDIO_RATE = 24000        # Sample rate (24000 is required by OpenAI)
CHUNK_SIZE = 1024         # Buffer size (smaller = lower latency, larger = more stable)

# System settings
REENGAGE_DELAY_MS = 300   # Delay before microphone re-engages after AI speaks

def get_optimized_settings():
    """Get optimized settings based on your system"""
    return {
        'mic_gain': MIC_GAIN_MULTIPLIER,
        'min_level': MIN_AUDIO_LEVEL,
        'speech_threshold': SPEECH_DETECTION_THRESHOLD,
        'silence_duration': SILENCE_DURATION_MS,
        'prefix_padding': PREFIX_PADDING_MS,
        'rate': AUDIO_RATE,
        'chunk_size': CHUNK_SIZE,
        'reengage_delay': REENGAGE_DELAY_MS
    }

def print_current_settings():
    """Print current audio settings"""
    settings = get_optimized_settings()
    print("🔧 Current Audio Settings:")
    print(f"   Microphone Gain: {settings['mic_gain']}x")
    print(f"   Minimum Audio Level: {settings['min_level']}")
    print(f"   Speech Detection Threshold: {settings['speech_threshold']}")
    print(f"   Silence Duration: {settings['silence_duration']}ms")
    print(f"   Audio Rate: {settings['rate']}Hz")
    print(f"   Chunk Size: {settings['chunk_size']}")
    print()
    print("💡 Tips:")
    if settings['mic_gain'] > 2.0:
        print("   - High microphone gain may cause distortion")
    if settings['speech_threshold'] < 0.3:
        print("   - Low speech threshold may pick up background noise")
    if settings['silence_duration'] < 500:
        print("   - Short silence duration may cut off slow speech")
    print("   - Adjust MIC_GAIN_MULTIPLIER in audio_settings.py if audio is too quiet/loud")
    print("   - Lower SPEECH_DETECTION_THRESHOLD if AI doesn't detect your speech")
    print("   - Increase SILENCE_DURATION_MS if AI cuts you off too quickly")

if __name__ == "__main__":
    print_current_settings()