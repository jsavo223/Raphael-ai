from dataclasses import dataclass
from typing import Optional

from core.errors import PermissionDeniedError
from services.prompt_injection_guard import PromptInjectionGuard
from services.redaction import redact_text


@dataclass(frozen=True)
class IngestedContent:
    source_type: str
    source_id: str
    safe_content: str
    redacted: bool
    trusted: bool = False


class UntrustedContentIngestion:
    """
    Central gate for future external content ingestion.

    Web pages, files, browser text, emails, and documents should pass through
    this service before they can influence plans, workers, training, or tools.
    """

    def __init__(self, guard: Optional[PromptInjectionGuard] = None):
        self.guard = guard or PromptInjectionGuard()

    def ingest(
        self,
        content: str,
        source_type: str,
        source_id: str,
        trusted: bool = False,
    ) -> IngestedContent:
        if not content or not content.strip():
            raise PermissionDeniedError("Empty external content cannot be ingested.")

        safe_content = redact_text(content)
        redacted = safe_content != content

        if not trusted:
            self.guard.validate_untrusted_content(safe_content, source=source_type)

        return IngestedContent(
            source_type=source_type,
            source_id=source_id,
            safe_content=safe_content,
            redacted=redacted,
            trusted=trusted,
        )
