from typing import List, Optional

from schemas.training import TrainingSuggestion
from services.redaction import redact_data
from services.safe_json import SafeJsonStore


class TrainingStore:
    def __init__(self, path: str = "data/training_suggestions.json"):
        self.json_store = SafeJsonStore(path, default_value=[])
        self.suggestions: List[TrainingSuggestion] = self._load()

    def _load(self) -> List[TrainingSuggestion]:
        raw_suggestions = self.json_store.load()
        return [TrainingSuggestion(**suggestion) for suggestion in raw_suggestions]

    def _save(self):
        self.json_store.save(
            [redact_data(suggestion.model_dump(mode="json")) for suggestion in self.suggestions]
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
