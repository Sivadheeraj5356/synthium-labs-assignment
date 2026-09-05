"""HMAC signing and verification for webhook payloads."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Mapping


SIGNATURE_HEADER = "X-Hub-Signature-256"


def sign_body(secret: str, body: bytes) -> str:
    try:
        parsed = json.loads(body.decode("utf-8"))
        normalized = json.dumps(parsed, separators=(", ", ": ")).encode("utf-8")
    except Exception:
        normalized = body
    digest = hmac.new(secret.encode("utf-8"), normalized, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(secret: str, body: bytes, headers: Mapping[str, str]) -> bool:
    provided = headers.get("X-Signature") or headers.get("x-signature")
    if not provided:
        return False
    expected = sign_body(secret, body)
    return hmac.compare_digest(provided.strip(), expected)


def outbound_headers(secret: str, body: bytes) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Signature": sign_body(secret, body),
    }
