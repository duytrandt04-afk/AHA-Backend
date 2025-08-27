import dspy
from pydantic import BaseModel
from typing import Optional, List, Dict, Union

class DiarizedAudio(BaseModel):
    diarization: List[Dict[str, Union[str, float]]]
    speech_audio_base64: str

class Message(BaseModel):   
    content: Optional[str] = None
    images: Optional[List[Union[str, dspy.Image]]] = None
    context: Optional[List[str]] = None
    recent_conversations: Optional[List[str]] = None
    files: Optional[List[str]] = None
    audio: Optional[List[DiarizedAudio]] = None