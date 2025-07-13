import os
import logging # Import logging
from typing import Any, Dict, List, Optional
from google import genai
from .config import ModelSectionConfig # Import ModelSectionConfig

class ModelCallError(Exception):
    """Custom exception for errors during model calls."""
    pass

class ModelClient:
    """
    Handles interactions with the Gemini API for various model calls.
    """
    def __init__(self, config: ModelSectionConfig): # Accept ModelSectionConfig
        self.config = config
        self.logger = logging.getLogger(__name__) # Get logger for ModelClient
        try:
            api_key = os.environ.get(self.config.api_key_env)
            if not api_key:
                raise ValueError(f"Environment variable '{self.config.api_key_env}' not set.")
            self._client = genai.Client(api_key=api_key)
        except Exception as e:
            self.logger.error("Error initializing Gemini client: %s", e)
            raise ValueError(f"Error initializing Gemini client: {e}")

    def call_model(
        self,
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        dry_run: bool = False,
        **kwargs # For any other model-specific parameters
    ) -> str:
        """
        Makes a call to the specified Gemini model with prompt and system prompt.
        """
        if dry_run:
            self.logger.info(f"Dry run: Model '{model_name}' would be called with prompt:\n{prompt}")
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
            self.logger.error("Failed to call model '%s': %s", model_name, e)
            raise ModelCallError(f"Failed to call model '{model_name}': {e}")
