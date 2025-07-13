# self_improvement.py
import subprocess
from pathlib import Path
import os
from google import genai

from god_engine.goal_manager import GoalManager
from god_engine.problem_identification import generate_goals_from_todos


class SelfImprovementModule:
    """
    Orchestrates dynamic goal management, problem identification,
    and Gemini-driven patch generation focused on capability & autonomy.
    """

    def __init__(self, cfg: dict):
        # Load config
        self.code_dir = Path(cfg["code_dir"])
        self.mem_file = Path(cfg["memory_path"])
        self.max_cycles = cfg["max_cycles"]
        # Init goal manager
        self.goals = GoalManager(cfg.get("goals_path", "goals.json"))
        # Bootstrap any new TODOs as goals by analyzing the codebase
        new_goals = generate_goals_from_todos(str(self.code_dir))
        for goal_data in new_goals:
            if not any(g.goal_id == goal_data["id"] for g in self.goals.goals):
                self.goals.add_goal_from_dict(goal_data)

        # Gemini client setup
        try:
            self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error configuring Gemini: {e}")
            self.client = None
        # Memory of applied goals
        self.memory = (
            set(self.mem_file.read_text(encoding="utf-8").splitlines())
            if self.mem_file.exists()
            else set()
        )

    def save_memory(self):
        self.mem_file.write_text("\n".join(self.memory), encoding="utf-8")

    def call_gemini(self, prompt: str) -> str:
        """
        Send a feature-driven request to Gemini and return the unified-diff patch.
        """
        if not self.client:
            return ""
        # Ensure your GEMINI_API_KEY is.
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        # Gemini returns a list of predictions; we expect one unified diff
        content = response.text
        if content is None:
            return ""
        # Some trimming/hygiene: ensure it starts with diff header
        if not content.startswith("diff") and "+++" in content:
            # try to locate first '+++'
            idx = content.find("+++")
            content = content[idx:]
        return content

    def improve(self):
        """
        Main loop for the self-improvement process.
        """
        print("Starting self-improvement cycle...")
        for i in range(self.max_cycles):
            print(f"\n--- Cycle {i + 1}/{self.max_cycles} ---")
            goal = self.goals.next_goal()
            if not goal:
                print("No more pending goals. Exiting.")
                break

            print(f"Selected goal: {goal.goal_id} - {goal.description}")

            if goal.goal_id in self.memory:
                print("Goal already attempted. Skipping.")
                continue

            prompt = (
                f"# Goal ID: {goal.goal_id}\n"
                f"# Description: {goal.description}\n"
                "Generate a unified-diff patch to implement this "
                "capability, prioritizing autonomy and resilience.\n"
                f"# Base path: {self.code_dir}\n"
            )
            print("Generating patch with Gemini...")
            patch = self.call_gemini(prompt)

            if not patch:
                print("Gemini returned no patch. Skipping goal.")
                self.memory.add(goal.goal_id)
                continue

            print(f"Applying patch:\n{patch}")
            applied = self.apply_patch(patch)
            if applied:
                print("Patch applied successfully. Running tests...")
                if self.run_tests():
                    print("Tests passed. Marking goal as done.")
                    self.goals.mark_done(goal.goal_id)
                else:
                    print("Tests failed. Reverting patch.")
                    self.git_reset_all()
            else:
                print("Failed to apply patch.")

            self.memory.add(goal.goal_id)

        print("\nSelf-improvement cycle finished.")
        self.save_memory()
        self.goals.save()

    def apply_patch(self, patch_text: str) -> bool:
        """Applies a patch to the codebase."""
        if not patch_text:
            return False
        try:
            # Create a temporary patch file in the current working directory (root)
            patch_file_path = Path("./temp.patch")
            patch_file_path.write_text(patch_text, encoding="utf-8")

            # Apply the patch using git from the project root
            subprocess.run(
                ["git", "apply", str(patch_file_path)],
                check=True,
                cwd=".",  # Execute from the current working directory (project root)
                capture_output=True,
            )
            patch_file_path.unlink()  # Delete the temporary patch file
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error applying patch: {e}")
            if isinstance(e, subprocess.CalledProcessError):
                print(e.stderr.decode())
            return False

    def run_tests(self) -> bool:
        """Runs the test suite."""
        try:
            subprocess.run(
                ["pytest"], check=True, cwd=".", capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Tests failed: {e}")
            print(e.stderr.decode())
            return False

    def git_reset_all(self):
        """Resets all changes in the git repository."""
        try:
            subprocess.run(
                ["git", "reset", "--hard"],
                check=True,
                cwd=".",
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error resetting git: {e}")
            print(e.stderr.decode())
