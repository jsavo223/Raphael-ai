import json
from pathlib import Path
from typing import List, Optional

from schemas.training import TrainingSuggestion
from services.redaction import redact_data


class TrainingStore:
    def __init__(self, path: str = "data/training_suggestions.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.suggestions: List[TrainingSuggestion] = self._load()

    def _load(self) -> List[TrainingSuggestion]:
        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as file:
            raw_suggestions = json.load(file)

        return [TrainingSuggestion(**suggestion) for suggestion in raw_suggestions]

    def _save(self):
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                [redact_data(suggestion.model_dump(mode="json")) for suggestion in self.suggestions],
                file,
                indent=2,
            )

    def add(self, suggestion: TrainingSuggestion):
        redacted_suggestion = TrainingSuggestion(
            **redact_data(suggestion.model_dump(mode="json"))
        )
        self.suggestions.append(redacted_suggestion)
        self._save()
        return redacted_suggestion

    def get_all(self):
        return self.suggestions

    def get(self, suggestion_id: str) -> Optional[TrainingSuggestion]:
        for suggestion in self.suggestions:
            if suggestion.suggestion_id == suggestion_id:
                return suggestion
        return None

    def update(self, suggestion: TrainingSuggestion):
        redacted_suggestion = TrainingSuggestion(
            **redact_data(suggestion.model_dump(mode="json"))
        )

        for index, existing in enumerate(self.suggestions):
            if existing.suggestion_id == redacted_suggestion.suggestion_id:
                self.suggestions[index] = redacted_suggestion
                self._save()
                return redacted_suggestion

        return self.add(redacted_suggestion)
