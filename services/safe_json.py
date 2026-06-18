import json
from pathlib import Path
from typing import Any


class CorruptJsonRecoveredError(Exception):
    """Raised when a corrupt JSON file is moved aside and reset."""


class SafeJsonStore:
    """
    Shared JSON file helper for early-stage local storage.

    It provides:
    - parent directory creation
    - atomic-style writes using a temporary file then replace
    - corrupt-file recovery by moving bad JSON aside
    """

    def __init__(self, path: str, default_value: Any):
        self.path = Path(path)
        self.default_value = default_value
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return self.default_value

        try:
            with self.path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            corrupt_path = self.path.with_suffix(self.path.suffix + ".corrupt")
            self.path.replace(corrupt_path)
            self.save(self.default_value)
            return self.default_value

    def save(self, value: Any):
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")

        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(value, file, indent=2)

        temp_path.replace(self.path)
        return value
