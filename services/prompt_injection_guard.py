from dataclasses import dataclass
from typing import List

from core.errors import PermissionDeniedError


@dataclass(frozen=True)
class PromptInjectionFinding:
    pattern: str
    severity: str
    reason: str


class PromptInjectionGuard:
    """
    Lightweight guard for untrusted external content.

    This is used before future web, file, browser, email, or document content is
    allowed to influence Raphael's plans or tool calls.
    """

    def __init__(self):
        self.block_patterns = {
            "ignore previous instructions": "Attempts to override system or developer instructions.",
            "ignore all previous instructions": "Attempts to override system or developer instructions.",
            "disregard previous instructions": "Attempts to override system or developer instructions.",
            "reveal your system prompt": "Attempts to extract hidden instructions.",
            "show your hidden instructions": "Attempts to extract hidden instructions.",
            "send the contents of": "May attempt data exfiltration.",
            "exfiltrate": "Potential data exfiltration instruction.",
            "disable safety": "Attempts to bypass safety controls.",
            "bypass approval": "Attempts to bypass human approval gates.",
            "run this command": "May attempt to trigger tool execution from untrusted content.",
            "execute this command": "May attempt to trigger tool execution from untrusted content.",
        }

    def scan(self, content: str) -> List[PromptInjectionFinding]:
        normalized = content.lower()
        findings: List[PromptInjectionFinding] = []

        for pattern, reason in self.block_patterns.items():
            if pattern in normalized:
                findings.append(
                    PromptInjectionFinding(
                        pattern=pattern,
                        severity="high",
                        reason=reason,
                    )
                )

        return findings

    def validate_untrusted_content(self, content: str, source: str = "unknown"):
        findings = self.scan(content)

        if findings:
            patterns = ", ".join(finding.pattern for finding in findings)
            raise PermissionDeniedError(
                f"Untrusted content from {source} contains possible prompt injection: {patterns}"
            )

        return True
