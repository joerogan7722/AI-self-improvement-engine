import logging  # Import logging
import os
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from .config import ModelSectionConfig  # Import ModelSectionConfig


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
            genai.configure(api_key=api_key)
            self._configured = True
        except Exception as e:
            self.logger.error("Error configuring Gemini API: %s", e)
            raise ValueError(f"Error configuring Gemini API: {e}")

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
            # Create model instance
            model = genai.GenerativeModel(model_name)
            
            # Construct prompt with system prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

            response = model.generate_content(full_prompt, **kwargs)
            
            if response.text is None:
                raise ModelCallError(f"Model '{model_name}' returned no text response.")
            
            return response.text

        except Exception as e:
            self.logger.error("Failed to call model '%s': %s", model_name, e)
            raise ModelCallError(f"Failed to call model '{model_name}': {e}")
