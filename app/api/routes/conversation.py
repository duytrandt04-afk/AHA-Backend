import asyncio
import threading
import traceback
from app.schemas.message import Message
from app.utils import build_error_response
from fastapi import APIRouter, HTTPException
from app.models.text_to_speech import generate_audio
from app.models.speech_to_text import transcribe_audio
from app.utils.streaming import generate_response_stream
from app.services.manage_responses import ResponseManager
from fastapi.responses import JSONResponse, StreamingResponse
from app.services.real_time.realtime_client import RealtimeClient
from app.schemas.audio import Audio, Text, RealtimeResponse, RealtimeStartRequest, StatusResponse

# Create a router with a common prefix and tag for all conversation-related endpoints
router = APIRouter(prefix="/api/conversations", tags=["Conversations"])

@router.post("/generate_title")
async def generate_title(message: Message):
    """
    Generate a conversation title based on the user's initial message content or image.

    This endpoint uses a summarization model to produce a short, descriptive title
    for the beginning of a new conversation. It supports both text and image inputs.

    Args:
        user_id (str): The ID of the user initiating the conversation.
        request (Request): The incoming HTTP request containing the JSON body.
            Expected fields in JSON:
                - content (str, optional): User's text message.
                - files (list, optional): List of files; expects base64-encoded image at files[0].data.
                - timestamp (str, optional): Time the message was sent.

    Returns:
        JSONResponse: A JSON object with the generated title:
            {
                "title": "Short summary of message or image"
            }

    Error Responses:
        - 400: If user ID is not provided or input is invalid.
        - 500: If title generation fails due to internal error or model issues.
    """
    try:
        
        title = await ResponseManager.summarize(message)
        return JSONResponse(content={"title": title}, status_code=200)
    except Exception as e:
        traceback.print_exc
        return build_error_response(
            "TITLE_GENERATION_FAILED",
            f"Failed to generate title: {str(e)}",
            500
        )
    
@router.post("/stream")
async def stream_message(message: Message):
    """Return serialized stream chunks with full response"""
    try:
        response = await generate_response_stream(message=message)
        return response
        
    except Exception as e:
        traceback.print_exc()
        return build_error_response(
            "STREAM_INITIALIZATION_FAILED",
            f"Failed to initialize message stream: {str(e)}",
            500
        )

@router.post("/speech_to_text")
async def speech_to_text(request: Audio):
    """
    Transcribe the given audio file using Faster-Whisper.

    Args:
        request (Audio): Request containing base64-encoded audio data.

    Returns:
        str: The transcribed text from the audio file.
    """
    try:
        return await transcribe_audio(request.audio)
    except Exception as e:
        traceback.print_exc
        
@router.post("/text_to_speech")
async def text_to_speech(input: Text):
    if not input or not input.text:
        return build_error_response("INVALID_INPUT", "Input text is required", 400)

    # Return streaming response directly
    return StreamingResponse(
        generate_audio(input.text),
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'inline; filename="speech.mp3"'}
    )


# Global client instance
realtime_client: RealtimeClient = None
client_thread: threading.Thread = None

def run_client_in_thread(client: RealtimeClient):
    """Run the realtime client in a separate thread"""
    try:
        client.start()
    except Exception as e:
        print(f"Error running client: {e}")

@router.post("/realtime/start", response_model=RealtimeResponse)
async def start_realtime(request: RealtimeStartRequest):
    """Start the OpenAI Realtime voice chat"""
    global realtime_client, client_thread
    
    try:
        # Check if client is already running
        if realtime_client and realtime_client.is_active():
            return RealtimeResponse(
                status="already_running",
                message="Realtime client is already active",
                client_active=True
            )
        
        # Create new client instance
        realtime_client = RealtimeClient()
        
        # Start client in a separate thread
        client_thread = threading.Thread(target=run_client_in_thread, args=(realtime_client,))
        client_thread.daemon = True
        client_thread.start()
        
        # Give it a moment to initialize
        await asyncio.sleep(1)
        
        return RealtimeResponse(
            status="success",
            message="Realtime voice chat started successfully",
            client_active=realtime_client.is_active()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start realtime client: {str(e)}")

@router.post("/realtime/stop", response_model=RealtimeResponse)
async def stop_realtime():
    """Stop the OpenAI Realtime voice chat"""
    global realtime_client, client_thread
    
    try:
        if not realtime_client:
            return RealtimeResponse(
                status="not_running",
                message="Realtime client is not running",
                client_active=False
            )
        
        # Stop the client
        realtime_client.stop()
        
        # Wait for thread to finish (with timeout)
        if client_thread and client_thread.is_alive():
            client_thread.join(timeout=5)
        
        return RealtimeResponse(
            status="success",
            message="Realtime voice chat stopped successfully",
            client_active=False
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop realtime client: {str(e)}")

# Cleanup on shutdown
@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup when server shuts down"""
    global realtime_client
    if realtime_client:
        realtime_client.stop()