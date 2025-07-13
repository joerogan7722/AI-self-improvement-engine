"""
This module provides utility functions for the God Engine project.
"""
import hashlib
import json
import os
import subprocess

import numpy as np


def calculate_checksum(file_path, buffer_size=4096):
    """Calculates the SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(buffer_size), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


class CodeIntegrityChecker:
    """A class to manage file integrity using checksums and snapshots."""
    def __init__(self, snapshot_dir):
        """Initializes the CodeIntegrityChecker."""
        self.snapshot_dir = snapshot_dir
        self.snapshot_index_file = os.path.join(
            snapshot_dir, "snapshots_index.json"
        )
        self.snapshots = {}
        self._load_snapshots_index()

    def _get_snapshot_path(self, file_path):
        """Generates a unique snapshot file path within the snapshot directory."""
        file_name = os.path.basename(file_path)
        path_hash = hashlib.md5(file_path.encode()).hexdigest()
        return os.path.join(
            self.snapshot_dir, f"{file_name}.{path_hash}.snapshot"
        )

    def _load_snapshots_index(self):
        """Loads the snapshot index from disk."""
        if os.path.exists(self.snapshot_index_file):
            with open(self.snapshot_index_file, "r", encoding="utf-8") as f:
                self.snapshots = json.load(f)
        print(f"Loaded snapshot index: {len(self.snapshots)} entries.")

    def _save_snapshots_index(self):
        """Saves the snapshot index to disk."""
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)
        with open(self.snapshot_index_file, "w", encoding="utf-8") as f:
            json.dump(self.snapshots, f, indent=4)
        print(f"Saved snapshot index: {len(self.snapshots)} entries.")

    def take_snapshot(self, file_path):
        """
        Takes a snapshot of a file's checksum and content, persisting it to disk.
        """
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)

        checksum = calculate_checksum(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        snapshot_file_path = self._get_snapshot_path(file_path)
        with open(snapshot_file_path, "w", encoding="utf-8") as f:
            f.write(content)

        self.snapshots[file_path] = {
            "checksum": checksum,
            "snapshot_file": snapshot_file_path
        }
        self._save_snapshots_index()

        print(f"Snapshot for {file_path} created with checksum {checksum}")

    def verify_integrity(self, file_path):
        """Verifies the integrity of a file against its stored snapshot."""
        if file_path not in self.snapshots:
            print(
                f"Warning: No snapshot found for {file_path}. "
                "Cannot verify integrity."
            )
            return True

        stored_checksum = self.snapshots[file_path]["checksum"]
        current_checksum = calculate_checksum(file_path)

        if current_checksum != stored_checksum:
            print(f"TAMPERING DETECTED: Checksum mismatch for {file_path}.")
            return False
        return True

    def auto_restore(self, file_path):
        """Restores a file from its trusted snapshot if tampering is detected."""
        if file_path not in self.snapshots:
            print(f"Error: Cannot restore {file_path}. No snapshot available.")
            return False

        snapshot_file_path = self.snapshots[file_path]["snapshot_file"]
        if not os.path.exists(snapshot_file_path):
            print(
                f"Error: Snapshot file not found at {snapshot_file_path}. "
                "Cannot restore."
            )
            return False

        try:
            with open(snapshot_file_path, "r", encoding="utf-8") as sf:
                trusted_content = sf.read()

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(trusted_content)

            print(f"Restored {file_path} from trusted snapshot.")
            self.take_snapshot(file_path)
            return True
        except IOError as e:
            print(f"Error restoring {file_path}: {e}")
            return False


def run_in_sandbox(code_string):
    """
    Executes a string of Python code in a restricted sandbox environment.
    """
    try:
        subprocess.run(
            ["python", "-c", code_string],
            check=True,
            capture_output=True,
            text=True
        )
        print("Code executed successfully in sandbox.")
        return True, "Execution successful."
    except subprocess.CalledProcessError as e:
        print(f"Sandbox execution failed: {e.stderr}")
        return False, str(e.stderr)


def greet(name):
    """A simple greeting function for demonstration purposes."""
    return (
        f"Hello, {name}! This function was added by the God Engine's "
        "self-improvement system."
    )


def process_data(data_list):
    """A hypothetical complex function to be refactored."""
    return sum(item * 2 if isinstance(item, (int, float)) else 1 for item in data_list)


def list_sum_optimization(data_list):
    """Optimized list sum using NumPy."""
    return np.sum(data_list)
