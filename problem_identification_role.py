# roles/problem_identification.py
from typing import Any
from ..engine import Role, Context

class ProblemIdentificationRole(Role):
    def __init__(self, model_client, prompt_template: str):
        self.model_client = model_client
        self.prompt_template = prompt_template

    def run(self, context: Context) -> Context:
        """
        Reads context.goal.description, uses model to generate a list of todos/tasks.
        """
        goal_desc = context.goal.get('description')
        prompt = self.prompt_template.format(goal_description=goal_desc)
        response = self.model_client.chat(prompt)
        # Assuming response is a newline-delimited list of tasks
        todos = [line.strip() for line in response.splitlines() if line.strip()]
        context.todos = todos
        return context
