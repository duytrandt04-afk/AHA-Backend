import time
import queue
import threading
import pyaudio
import numpy as np
from .config import Config

class AudioManager:
    def __init__(self):
        self.config = Config()
        self.audio_buffer = bytearray()
        self.mic_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        self.mic_on_at = 0
        self.mic_active = None
        self.is_playing = False
        
        self.p = pyaudio.PyAudio()
        self.mic_stream = None
        self.speaker_stream = None
        
        # Debug counters
        self.mic_frames_received = 0
        self.last_audio_level_check = time.time()
        
    def clear_audio_buffer(self):
        """Clear the audio buffer"""
        self.audio_buffer = bytearray()
        print('🔵 Audio buffer cleared.')
        
    def stop_audio_playback(self):
        """Stop audio playback"""
        self.is_playing = False
        print('🔵 Stopping audio playback.')
        
    def mic_callback(self, in_data, frame_count, time_info, status):
        """Handle microphone input and put it into a queue"""
        # Debug: Count frames and check audio levels
        self.mic_frames_received += 1
        
        # Check audio level every second
        current_time = time.time()
        if current_time - self.last_audio_level_check > 1.0:
            try:
                audio_data = np.frombuffer(in_data, dtype=np.int16)
                # Avoid division by zero and handle edge cases
                if len(audio_data) > 0:
                    audio_squared = audio_data.astype(np.float64) ** 2
                    mean_squared = np.mean(audio_squared)
                    rms = np.sqrt(max(mean_squared, 0.0))  # Ensure non-negative
                    print(f'🎤 Mic frames: {self.mic_frames_received}, Audio level: {rms:.0f}')
                    
                    # Check if audio levels are too low
                    if rms < 100:
                        print(f'⚠️  Low audio level detected. Try speaking louder or closer to microphone.')
                else:
                    print(f'🎤 Mic frames: {self.mic_frames_received}, Audio level: No data')
                    
                self.last_audio_level_check = current_time
            except Exception as e:
                print(f'Error calculating audio level: {e}')
        
        # Always process microphone input regardless of timing
        if self.mic_active != True:
            print('🎙️🟢 Mic active')
            self.mic_active = True
        
        # Apply gain boost to microphone input if needed
        try:
            if self.config.mic_gain_multiplier != 1.0:
                audio_data = np.frombuffer(in_data, dtype=np.int16)
                # Apply gain boost
                boosted_audio = audio_data * self.config.mic_gain_multiplier
                # Prevent clipping
                boosted_audio = np.clip(boosted_audio, -32767, 32767)
                # Convert back to bytes
                in_data = boosted_audio.astype(np.int16).tobytes()
        except Exception as e:
            print(f'Error applying mic gain: {e}')
        
        # Put audio data in queue immediately
        self.mic_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def speaker_callback(self, in_data, frame_count, time_info, status):
        """Handle audio playback callback"""
        bytes_needed = frame_count * 2
        current_buffer_size = len(self.audio_buffer)

        if current_buffer_size >= bytes_needed:
            audio_chunk = bytes(self.audio_buffer[:bytes_needed])
            self.audio_buffer = self.audio_buffer[bytes_needed:]
            self.mic_on_at = time.time() + self.config.reengage_delay_ms / 1000
        else:
            audio_chunk = bytes(self.audio_buffer) + b'\x00' * (bytes_needed - current_buffer_size)
            self.audio_buffer.clear()

        return (audio_chunk, pyaudio.paContinue)
    
    def start_streams(self):
        """Start audio streams"""
        try:
            print(f"🎤 Initializing audio streams...")
            print(f"   Format: {self.config.format}")
            print(f"   Rate: {self.config.rate}")
            print(f"   Chunk size: {self.config.chunk_size}")
            
            # List available audio devices for debugging
            print("Available audio devices:")
            for i in range(self.p.get_device_count()):
                info = self.p.get_device_info_by_index(i)
                print(f"  {i}: {info['name']} - Input: {info['maxInputChannels']}, Output: {info['maxOutputChannels']}")
            
            self.mic_stream = self.p.open(
                format=self.config.format,
                channels=1,
                rate=self.config.rate,
                input=True,
                stream_callback=self.mic_callback,
                frames_per_buffer=self.config.chunk_size,
                input_device_index=None  # Use default device
            )

            self.speaker_stream = self.p.open(
                format=self.config.format,
                channels=1,
                rate=self.config.rate,
                output=True,
                stream_callback=self.speaker_callback,
                frames_per_buffer=self.config.chunk_size,
                output_device_index=None  # Use default device
            )
            
            self.mic_stream.start_stream()
            self.speaker_stream.start_stream()
            
            print("✅ Audio streams started successfully!")
            
        except Exception as e:
            print(f"❌ Error starting audio streams: {e}")
            raise
        
    def stop_streams(self):
        """Stop audio streams and cleanup"""
        if self.mic_stream:
            self.mic_stream.stop_stream()
            self.mic_stream.close()
        if self.speaker_stream:
            self.speaker_stream.stop_stream()
            self.speaker_stream.close()
        
        self.p.terminate()
        print('Audio streams stopped and resources released.')
        
    def add_audio_data(self, audio_data):
        """Add audio data to buffer"""
        self.audio_buffer.extend(audio_data)
        print(f'🔵 Received {len(audio_data)} bytes, total buffer size: {len(self.audio_buffer)}')
        
    def is_streams_active(self):
        """Check if streams are active"""
        return (self.mic_stream and self.mic_stream.is_active() and 
                self.speaker_stream and self.speaker_stream.is_active())