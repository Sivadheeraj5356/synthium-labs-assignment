"""HMAC signing and verification for webhook payloads."""

from __future__ import annotations

import hashlib
import hmac
from typing import Mapping


SIGNATURE_HEADER = "X-Hub-Signature-256"


def sign_body(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(secret: str, body: bytes, headers: Mapping[str, str]) -> bool:
    provided = (
        headers.get(SIGNATURE_HEADER)
        or headers.get(SIGNATURE_HEADER.lower())
        or headers.get("X-Hub-Signature-256")
    )
    if not provided:
        return False
    expected = sign_body(secret, body)
    return hmac.compare_digest(provided.strip(), expected)


def outbound_headers(secret: str, body: bytes) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        SIGNATURE_HEADER: sign_body(secret, body),
    }
