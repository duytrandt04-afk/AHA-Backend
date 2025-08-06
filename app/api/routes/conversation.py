import json
import traceback
from fastapi import APIRouter
from app.schemas.message import Message
from app.schemas.audio import Audio, Text
from app.utils import build_error_response
from app.models.text_to_speech import generate_audio
from app.models.speech_to_text import transcribe_audio
from app.utils.streaming import generate_response_stream
from app.services.manage_responses import ResponseManager
from fastapi.responses import StreamingResponse, JSONResponse

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
def text_to_speech(input: Text):
    try:
        return StreamingResponse(
            generate_audio(text=input.text),
            media_type="audio/mpeg",
            headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control"
                }
        )
    except Exception as e:
        traceback.print_exc