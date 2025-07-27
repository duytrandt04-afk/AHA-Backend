from pydantic import BaseModel
from typing import Optional, List, Tuple

class Message(BaseModel):   
    content: Optional[str] = None
    images: Optional[List[str]] = None
    context: Optional[List[str]] = None
    recent_conversations: Optional[List[Tuple[str, str]]] = None # Recent conversations as a list of tuples (user_message, bot_response)