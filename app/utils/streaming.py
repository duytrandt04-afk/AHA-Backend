import dspy
from app.schemas.message import Message
from app.services.manage_responses import TextHandler

async def generate_response_stream(message: Message):
    try:
        handler = TextHandler()
        output_stream = await handler.handle_text_response(input_data=message)
        return {"response": output_stream}
                
    except ValueError as ve:
        return {
            "type": "error",
            "message": f"Invalid input: {str(ve)}"
        }
    except Exception as e:
        return {
            "type": "error",
            "message": f"Stream processing failed: {str(e)}"
        }
