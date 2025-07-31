import dspy
from app.schemas.message import Message
from app.services.manage_responses import TextHandler

async def generate_response_stream(message: Message):
    try:
        full_response = ""
        handler = TextHandler()
        output_stream = await handler.handle_text_response(input_data=message)
        
        # Stream the response output
        async for chunk in output_stream:
            if isinstance(chunk, dspy.streaming.StreamResponse):
                full_response += str(chunk.chunk)
                yield {
                    "type": "chunk",
                    "data": str(chunk.chunk),
                    "full_response_so_far": full_response
                }
            elif isinstance(chunk, dspy.Prediction):
                yield {
                    "type": "done", 
                    "data": "",
                    "full_response": chunk.response
                }
                
    except ValueError as ve:
        yield f"data: ERROR - Invalid input: {str(ve)}\n\n"
    except Exception as e:
        yield f"data: ERROR - Stream processing failed: {str(e)}\n\n"