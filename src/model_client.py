import os
from typing import Any, Dict, List, Optional
from google import genai

class ModelCallError(Exception):
    """Custom exception for errors during model calls."""
    pass

class ModelClient:
    """
    Handles interactions with the Gemini API for various model calls.
    """
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            self._client = genai.Client(api_key=api_key)
        else:
            try:
                self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            except KeyError:
                raise ValueError("GEMINI_API_KEY environment variable not set.")
            except Exception as e:
                raise ValueError(f"Error initializing Gemini client: {e}")

    def call_model(
        self,
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        # Removed optional generation parameters for now to debug
        dry_run: bool = False,
        **kwargs # For any other model-specific parameters
    ) -> str:
        """
        Makes a call to the specified Gemini model with only essential parameters.
        """
        if dry_run:
            print(f"Dry run: Model '{model_name}' would be called with prompt:\n{prompt}")
            return "DRY_RUN_RESPONSE"

        try:
            # Construct contents based on system_prompt presence
            contents = []
            if system_prompt:
                contents.append({"role": "user", "parts": [{"text": system_prompt}]})
                contents.append({"role": "model", "parts": [{"text": "Okay, I understand."}]}) # Standard response to system prompt
            contents.append({"role": "user", "parts": [{"text": prompt}]})

            response = self._client.models.generate_content(
                model=model_name, # Pass model_name as a keyword argument
                contents=contents,
                **kwargs # Pass any remaining kwargs directly to generate_content
            )
            
            if response.text is None:
                raise ModelCallError(f"Model '{model_name}' returned no text response.")
            
            return response.text

        except Exception as e:
            raise ModelCallError(f"Failed to call model '{model_name}': {e}")
