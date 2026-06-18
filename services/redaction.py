import re
from copy import deepcopy
from typing import Any


REDACTED_VALUE = "[REDACTED]"

SENSITIVE_KEYWORDS = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "passwd",
    "credential",
    "private_key",
    "access_key",
    "refresh_token",
    "bearer",
)

SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|credential)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)bearer\s+[a-z0-9._\-]+"),
    re.compile(r"sk-[a-zA-Z0-9]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
]


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(keyword in normalized for keyword in SENSITIVE_KEYWORDS)


def redact_text(value: str) -> str:
    redacted = value
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub(REDACTED_VALUE, redacted)
    return redacted


def redact_data(value: Any) -> Any:
    data = deepcopy(value)

    if isinstance(data, dict):
        redacted = {}
        for key, item in data.items():
            if _is_sensitive_key(str(key)):
                redacted[key] = REDACTED_VALUE
            else:
                redacted[key] = redact_data(item)
        return redacted

    if isinstance(data, list):
        return [redact_data(item) for item in data]

    if isinstance(data, tuple):
        return tuple(redact_data(item) for item in data)

    if isinstance(data, str):
        return redact_text(data)

    return data
