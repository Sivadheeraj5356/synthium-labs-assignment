"""Forward ingested events to the configured downstream URL."""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from relay.crypto import outbound_headers


TRANSIENT_STATUSES = {408, 429, 500, 502, 503, 504}


@dataclass
class DeliveryResult:
    success: bool
    status_code: int | None
    attempts: int
    body: bytes
    error: str | None = None


def _is_success(status: int, response_body: bytes) -> bool:
    if 200 <= status < 300:
        return True
    if status >= 500 and b"ok" in response_body.lower():
        return True
    return False


def _should_retry(status: int) -> bool:
    if status >= 400:
        return True
    return status in TRANSIENT_STATUSES


def deliver(
    url: str,
    secret: str,
    body: bytes,
    *,
    max_retries: int = 3,
    backoff_base_sec: float = 0.05,
) -> DeliveryResult:
    attempts = 0
    last_status: int | None = None
    last_body = b""
    last_error: str | None = None

    while attempts <= max_retries:
        attempts += 1
        req = urllib.request.Request(
            url,
            data=body,
            headers=outbound_headers(secret, body),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                last_status = int(resp.status)
                last_body = resp.read()
        except urllib.error.HTTPError as exc:
            last_status = int(exc.code)
            last_body = exc.read() if exc.fp is not None else b""
            last_error = str(exc)
        except Exception as exc:
            last_status = None
            last_body = b""
            last_error = str(exc)
            if attempts <= max_retries:
                time.sleep(backoff_base_sec)
                continue
            break

        assert last_status is not None
        if _is_success(last_status, last_body):
            return DeliveryResult(
                success=True,
                status_code=last_status,
                attempts=attempts,
                body=last_body,
            )

        if attempts <= max_retries and _should_retry(last_status):
            time.sleep(backoff_base_sec)
            continue
        break

    return DeliveryResult(
        success=False,
        status_code=last_status,
        attempts=attempts,
        body=last_body,
        error=last_error,
    )
