import gc
import os
import io
import base64
import tempfile
from io import BytesIO
from pydub import AudioSegment
from typing import Optional, List, Union, Any
from app.models.llm_gateway import client
from app.api.database.redis_client import get_config

async def transcribe_audio(audio: str) -> str:
    """
    Transcribe base64-encoded audio using OpenAI Whisper API.
    
    Args:
        audio (str): Base64-encoded audio data (WAV or MP3).
    
    Returns:
        str: Transcribed text.
    """
    # Decode base64 to raw bytes
    audio_bytes = base64.b64decode(audio)

    # Save to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio.flush()
        temp_audio_path = temp_audio.name

    try:
        with open(temp_audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=get_config("stt_config").get("model"),
                file=audio_file
            )
            return response.text
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)


def audiosegment_to_base64(segment: AudioSegment) -> str:
    """Convert AudioSegment to base64 encoded WAV."""
    buffer = BytesIO()
    segment.export(buffer, format="wav")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    buffer.close()
    return encoded


def base64_to_audiosegment(b64_str: str) -> AudioSegment:
    """Decode base64 WAV into AudioSegment."""
    audio_bytes = base64.b64decode(b64_str)
    return AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")


def format_time(seconds: float) -> str:
    """Format seconds to HH:MM:SS.mmm format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours:02d}:{minutes:02d}:{seconds%60:06.3f}"


async def process_diarization_segments_to_list_async(
    audio: Optional[List[Union[dict, Any]]],  # List of dicts or DiarizedAudio objects
) -> str:
    """
    Processes a list of diarized base64-encoded audio segments and transcribes each.

    Args:
        audio (Optional[List[dict]]): List of dicts with 'diarization' and 'speech_audio_base64',
                                    or DiarizedAudio objects.

    Returns:
        str: Full transcript across all diarized audio chunks.
    """
    if not audio:
        return "No audio input provided."

    all_results = []

    for index, item in enumerate(audio):
        # Handle both dict and DiarizedAudio objects
        if hasattr(item, 'diarization') and hasattr(item, 'speech_audio_base64'):
            # It's a DiarizedAudio object
            diarization = item.diarization
            speech_b64 = item.speech_audio_base64
        else:
            # It's a dict
            diarization = item.get("diarization")
            speech_b64 = item.get("speech_audio_base64")

        if diarization is None or not speech_b64:
            print(f"Skipping audio[{index}]: Missing diarization or base64 audio.")
            continue

        try:
            speech_only_audio = base64_to_audiosegment(speech_b64)
        except Exception as e:
            print(f"Failed to decode base64 audio for audio[{index}]: {e}")
            continue

        print(f"Processing diarization segments for audio[{index}]...")

        # Handle list of segment dictionaries
        for segment_dict in diarization:
            start_time = segment_dict["start"]
            end_time = segment_dict["end"]
            speaker = segment_dict["speaker"]
            
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)

            start_time_str = format_time(start_time)
            end_time_str = format_time(end_time)

            print(f"Segment: {start_time_str} - {end_time_str} ({speaker})")

            segment_audio = speech_only_audio[start_ms:end_ms]

            try:
                audio_base64 = audiosegment_to_base64(segment_audio)
                result_text = await transcribe_audio(audio_base64)
                chunk = f'[ {start_time_str} -- {end_time_str} ] {speaker} : {result_text}'
                all_results.append(chunk)
                print(f"Transcribed: {result_text[:50]}...")

            except Exception as e:
                print(f"Error at {start_time_str} - {end_time_str}: {e}")

            # Clean up memory
            del segment_audio
            gc.collect()

    final_result = "\n".join(all_results)
    print("✔ Done. Full transcription complete.")
    return final_result