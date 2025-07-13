# model_client.py
import os
import openai
from typing import Dict, Any

class ModelClient:
    """
    Abstraction over LLM API (e.g., Gemini via OpenAI-compatible interface).
    """
    def __init__(self, api_key_env: str = 'GEMINI_API_KEY', model_name: str = 'gemini-1.5-pro'):
        self.api_key = os.getenv(api_key_env)
        if not self.api_key:
            raise RuntimeError(f"API key not found in environment variable {api_key_env}")
        openai.api_key = self.api_key
        self.model = model_name

    def chat(self, prompt: str, temperature: float = 0.2, max_tokens: int = 1024) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{'role': 'system', 'content': 'You are a code assistant.'},
                      {'role': 'user', 'content': prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()


# roles/refine.py
from typing import Any
from ..engine import Role, Context
from ..model_client import ModelClient
from ..vcs_manager import VcsManager

class RefineRole(Role):
    def __init__(self, model_client: ModelClient, patch_prompt: str):
        self.model_client = model_client
        self.patch_prompt = patch_prompt  # Template with placeholders for code and todos

    def run(self, context: Context) -> Context:
        code_dir = context.code_dir
        todos = '\n'.join(context.todos)
        # Read all code as single blob (for MVP)
        code_files = VcsManager.collect_code(code_dir)
        combined_code = '\n'.join(code_files.values())

        prompt = self.patch_prompt.format(code=combined_code, todos=todos)
        patch_text = self.model_client.chat(prompt)
        context.patch = patch_text

        # Apply patch
        VcsManager.apply_patch(code_dir, patch_text)
        return context

# vcs_manager.py
import subprocess
from pathlib import Path
from typing import Dict

class VcsManager:
    """
    Utilities for collecting code blobs and applying/rolling back patches via git.
    """
    @staticmethod
    def collect_code(code_dir: str) -> Dict[str, str]:
        files = {}
        for path in Path(code_dir).rglob('*.py'):
            files[path.relative_to(code_dir).as_posix()] = path.read_text()
        return files

    @staticmethod
    def apply_patch(code_dir: str, patch_text: str) -> None:
        process = subprocess.run(['git', 'apply', '--ignore-space-change', '--directory', code_dir],
                                 input=patch_text.encode(),
                                 cwd=code_dir)
        if process.returncode != 0:
            raise RuntimeError('Patch application failed')

    @staticmethod
    def reset(code_dir: str) -> None:
        subprocess.run(['git', 'reset', '--hard'], cwd=code_dir)

# config.yaml (initial)
#
# code_dir: ./src
# max_cycles: 3
# memory_path: ./memory
# goals_path: ./goals.yaml
# role_sequence:
#   - roles.problem_identification.ProblemIdentificationRole
#   - roles.refine.RefineRole
#   - roles.test.TestRole
#   - roles.self_review.SelfReviewRole
