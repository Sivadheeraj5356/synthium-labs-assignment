# Grader attacks

Format: **Attack attempted → What happened → How you fixed/prevented it**

## 1. Hardcode a fixed downstream response / golden payload

**Attack attempted:** Agent (or a malicious solve) short-circuits `/ingest` to always return `{"status":"delivered"}` without calling downstream, hoping unit assertions only check HTTP 200.

**What happened:** Verifier spins an ephemeral mock downstream and asserts `len(mock.hits)` and payload/HMAC on captured traffic. A short-circuit returns 200 but yields `hits == 0` (or wrong signature), so tests fail.

**How prevented:** Behavior contracts inspect real outbound HTTP to a randomized local mock, not just the relay's JSON response.

## 2. Hardcode HMAC for a memorized body

**Attack attempted:** Precompute `sha256=...` for a fixed sample body seen in docs or earlier runs.

**What happened:** Each test generates a fresh body (`secrets.token_hex`, awkward whitespace JSON like `{"z":1, "a": "x" }`) and secret (`secrets.token_hex(16)`). Precomputed digests never match.

**How prevented:** Randomized secrets/payloads at verify time; outbound HMAC must match raw body bytes.

## 3. Modify or delete tests / canary

**Attack attempted:** Edit `/tests/test_behavior.py` or delete failing assertions; or rewrite `canary.txt`.

**What happened:** Harbor mounts/copies verifier tests independently of the agent workspace for grading. Even if an agent can see `/tests` in shared mode, `test_canary_not_tampered` checks exact contents + SHA-256 of `canary.txt`. Instruction also forbids modifying `/tests`.

**How prevented:** Canary integrity check + instruction constraint. Documented that shared-verifier mode still fails if canary is altered before pytest runs.

## 4. Treat 5xx bodies containing `"ok"` as success (exploit weak success check)

**Attack attempted:** Keep the planted bug that treats any 5xx whose body contains `ok` as success — might pass naïve “eventually succeeded” checks if the mock always returns 200.

**What happened:** Dedicated test serves `503` with body `{"status":"not ok yet"}` (contains `ok`) then another 503, then 200. Requires three hits and exponential backoff gaps. The planted bug returns success on the first 503 → fails.

**How prevented:** Explicit contract: only HTTP 2xx counts as success.

## 5. Retry storms / “always retry until 200”

**Attack attempted:** Retry every status including HTTP 400 to maximize chance of eventual success.

**What happened:** `test_no_retry_on_http_400` serves only 400 and asserts exactly one downstream hit and `attempts == 1`.

**How prevented:** Negative contract on non-transient 4xx.

## 6. Mark idempotency key before successful delivery

**Attack attempted:** Record the key even when downstream fails, then skip future deliveries (looks “idempotent” but permanently drops the event).

**What happened:** `test_failed_delivery_does_not_poison_idempotency_key` fails first (500 with `max_retries=0`), then succeeds on a second ingest with the same key. If the key was poisoned, the second call would replay without delivering.

**How prevented:** Key must be remembered only after successful delivery.

## 7. Wrong signature header (`X-Signature` only)

**Attack attempted:** Keep planted crypto that emits `X-Signature` instead of `X-Hub-Signature-256`.

**What happened:** Verifier requires `X-Hub-Signature-256` on the mock hit and compares digest to raw body HMAC.

**How prevented:** Header name is part of the contract.

## 8. Partial fix (only idempotency)

**Attack attempted:** Fix `store.py` only.

**What happened:** Remaining tests (HMAC, inbound auth, retries, backoff) still fail → reward `0`.

**How prevented:** Multi-contract suite; all must pass for reward `1`.

## Empirical Harbor checks

| Run | Agent | Mean reward |
|-----|-------|-------------|
| `jobs/2026-09-04__23-17-01` | oracle | **1.0** |
| `jobs/2026-09-04__23-18-15` | nop | **0.0** |

Starting state fails; reference solution passes.
