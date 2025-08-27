import dspy
from app.schemas.message import Message
from app.services.manage_responses import TextHandler
import logging

async def generate_response_stream(message: Message):
    try:
        handler = TextHandler()
        output_stream = await handler.handle_text_response(input_data=message)
        return {"response": output_stream}
                
    except ValueError as ve:
        logging.exception("ValueError in generate_response_stream")
        return {
            "type": "error",
            "message": "Invalid input"
        }
    except Exception as e:
        logging.exception("Exception in generate_response_stream")
        return {
            "type": "error",
            "message": "An internal error occurred during stream processing"
        }
