from pydub import AudioSegment
from pydantic import BaseModel
from typing import Optional, List, Any, Tuple

class Message(BaseModel):   
    content: Optional[str] = None
    images: Optional[List[str]] = None
    context: Optional[List[str]] = None
    recent_conversations: Optional[List[str]] = None
    files: Optional[List[str]] = None
    audio: Optional[List[str]] = None
    # audio: Optional[List[Tuple[Any, AudioSegment]]] = None
    
    class Config:
        arbitrary_types_allowed = True