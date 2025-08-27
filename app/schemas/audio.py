from pydantic import BaseModel

class Audio(BaseModel):
    audio: str
    
class Text(BaseModel):
    text: str
    
# Request/Response models
class RealtimeStartRequest(BaseModel):
    message: str = "Starting realtime voice chat"

class RealtimeResponse(BaseModel):
    status: str
    message: str
    client_active: bool = False

class StatusResponse(BaseModel):
    status: str
    client_active: bool
    message: str