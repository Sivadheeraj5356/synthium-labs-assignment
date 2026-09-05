# Webhook Relay

Small Python webhook ingest → downstream delivery relay.

```bash
export SHARED_SECRET=dev-secret
export DOWNSTREAM_URL=http://127.0.0.1:9000/hook
export REQUIRE_SIGNATURE=1
python -m relay --host 127.0.0.1 --port 8080
```

POST JSON to `/ingest` with headers:

- `Idempotency-Key` (required)
- `X-Hub-Signature-256: sha256=<hex>` when `REQUIRE_SIGNATURE=1`

Original educational code. MIT licensed.
