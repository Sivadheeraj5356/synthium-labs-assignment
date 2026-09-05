"""HTTP ingest server for the webhook relay."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from relay.config import Settings
from relay.crypto import verify_signature
from relay.deliver import deliver
from relay.store import IdempotencyStore


class RelayState:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = IdempotencyStore()


def make_handler(state: RelayState):  # noqa: ANN201
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def _read_body(self) -> bytes:
            length = int(self.headers.get("Content-Length", "0"))
            return self.rfile.read(length) if length > 0 else b""

        def _send(self, code: int, payload: dict[str, Any]) -> None:
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:  # noqa: N802
            if urlparse(self.path).path == "/health":
                self._send(200, {"status": "ok"})
                return
            self._send(404, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path != "/ingest":
                self._send(404, {"error": "not_found"})
                return

            body = self._read_body()
            headers = {k: v for k, v in self.headers.items()}
            idem = headers.get("Idempotency-Key") or headers.get("idempotency-key")
            if not idem:
                self._send(400, {"error": "missing_idempotency_key"})
                return

            settings = state.settings
            if not settings.downstream_url or not settings.shared_secret:
                self._send(500, {"error": "misconfigured"})
                return

            if settings.require_signature:
                if not verify_signature(settings.shared_secret, body, headers):
                    self._send(401, {"error": "invalid_signature"})
                    return

            try:
                json.loads(body.decode("utf-8"))
            except Exception:
                self._send(400, {"error": "invalid_json"})
                return

            def _deliver():
                return deliver(
                    settings.downstream_url,
                    settings.shared_secret,
                    body,
                    max_retries=settings.max_retries,
                    backoff_base_sec=settings.backoff_base_sec,
                )

            result = state.store.process(idem, _deliver)
            delivery = result.value
            if result.replayed:
                self._send(200, {"status": "replayed", "delivered": False})
                return

            if delivery is None or not getattr(delivery, "success", False):
                self._send(
                    502,
                    {
                        "status": "delivery_failed",
                        "attempts": getattr(delivery, "attempts", 0),
                        "downstream_status": getattr(delivery, "status_code", None),
                    },
                )
                return

            self._send(
                200,
                {
                    "status": "delivered",
                    "attempts": delivery.attempts,
                    "downstream_status": delivery.status_code,
                },
            )

    return Handler


def serve(host: str, port: int, settings: Settings | None = None) -> ThreadingHTTPServer:
    state = RelayState(settings or Settings.from_env())
    httpd = ThreadingHTTPServer((host, port), make_handler(state))
    return httpd
