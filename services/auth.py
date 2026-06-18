import os
import secrets
from typing import Optional

from fastapi import Header, HTTPException, status


OWNER_API_KEY_ENV = "RAPHAEL_OWNER_API_KEY"
OWNER_API_KEY_HEADER = "X-Raphael-Owner-Key"


def require_owner_api_key(
    owner_key: Optional[str] = Header(default=None, alias=OWNER_API_KEY_HEADER),
):
    expected_key = os.getenv(OWNER_API_KEY_ENV)

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Owner API key is not configured.",
        )

    if not owner_key or not secrets.compare_digest(owner_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing owner API key.",
        )

    return True
