import dspy
from typing import Optional, Union, List
from app.utils import create_signature_with_doc

class LLMResponse(dspy.Signature):
    recent_conversations: Optional[List[str]] = dspy.InputField(optional=True, description="Recent conversations")
    prompt: str = dspy.InputField(description="User's main prompt")
    files: Optional[List[str]] = dspy.InputField(description="Content extracted from pdf, csv, txt")
    audio: Optional[List[str]] = dspy.InputField(description="Content extracted from audio files")
    images: Optional[List[Union[str, dspy.Image]]] = dspy.InputField(optional=True, description="Images from user")
    response: str = dspy.OutputField()

class LLM(dspy.Module):
    """Model to generate general LLM responses."""
    predictor_cls = dspy.ChainOfThought

    def __init__(self, config: dict = None):
        self.model = config["model"]
        self.temperature = config["temperature"]    
        self.max_tokens = config["max_tokens"]

        # Create a unique signature class with a custom docstring
        self.signature_cls = create_signature_with_doc(LLMResponse, config["instruction"])

        self.response = self.predictor_cls(self.signature_cls, temperature=self.temperature, max_tokens=self.max_tokens)

    async def forward(
            self, 
            images: Optional[List[Union[str, dspy.Image]]] = None, 
            prompt: Optional[str] = None, 
            recent_conversations: Optional[List[str]] = None,
            files: Optional[List[str]]  = None,
            audio: Optional[List[str]] = None
        ) -> str:

        """
        Generate a model response based on the provided prompt, image, and optional conversation history.

        This method asynchronously invokes the response model (`self.response`) with the given inputs,
        which may include multimodal data (text + image) and previous responses for context.

        Args:
            image (Optional[dspy.Image], optional): An image input, if available (e.g., for visual Q&A or diagnosis).
            prompt (str, optional): The current user prompt or message.
            previous_reponses (str, optional): A string representing previous conversation turns to provide context.

        Returns:
            str: The generated response from the model.
        """
        response = await self.response.acall(
            prompt=prompt or "", 
            images=images or [], 
            recent_conversations=recent_conversations or [],
            files=files or [],
            audio=audio or []
        )
        return response.response