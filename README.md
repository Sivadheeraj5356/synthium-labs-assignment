# Synthium Labs Coding RL Environment — Harbor Webhook Relay

**Summary (for submission email):** A Harbor/Terminal-Bench 2.0 coding RL environment that evaluates whether an AI agent can debug a multi-file Python webhook relay. The starting repo has realistic bugs spanning idempotency, HMAC signing, inbound verification, and retry/backoff. An anti-reward-hack verifier uses randomized payloads, an ephemeral mock downstream, behavior contracts (not golden strings), and a canary file. Proven: `harbor run -a nop` → reward `0`; `harbor run -a oracle` → reward `1`.

## Synthium checklist mapping

Assignment asked for `task/instruction.md` + `task/task.yaml`. This repo includes those **and** keeps Harbor’s required root layout (`instruction.md`, `task.toml`) so `harbor run -p .` works out of the box. That dual layout is intentional.

```
coding-rl-environment/          # this repository root
├── task/
│   ├── instruction.md          # Synthium task definition (agent prompt copy)
│   └── task.yaml               # Synthium metadata + Q1–Q4 answers
├── instruction.md              # Harbor agent prompt (canonical for harbor run)
├── task.toml                   # Harbor runtime config (not YAML — Harbor requires TOML)
├── environment/
│   ├── Dockerfile
│   └── repo/                   # starting broken codebase (original, MIT)
├── solution/
│   ├── solve.sh                # reference / oracle solution
│   └── fixed/                  # known-good modules
├── tests/
│   ├── test.sh                 # verifier entry → /logs/verifier/reward.txt
│   ├── test_behavior.py
│   └── canary.txt
├── analysis/
│   ├── grader_attacks.md
│   └── model_runs.md
└── README.md
```

## 1. What did you build?

One production-style coding RL environment: **`synthium/webhook-relay`**, runnable with Harbor (official Terminal-Bench 2.0 harness).

## 2. What capability does it test?

Repository-level backend debugging: exactly-once delivery, cryptographic request authenticity, and correct retry classification/backoff across multiple files. See [`task/task.yaml`](task/task.yaml).

## 3. Why is this useful for evaluating a coding agent?

Agents must explore a realistic service, form hypotheses, and change several modules. Success is **live HTTP behavior**, not matching a prescribed diff — closer to real coding-agent work than LeetCode.

## 4. How do we run the environment?

Needs: Docker Desktop (running) + [Harbor](https://github.com/harbor-framework/harbor).

```bash
cd synthium-harbor-webhook   # or your clone path
harbor run -p . -a oracle
harbor run -p . -a nop
# optional, with a valid Anthropic key:
# harbor run -p . -a terminus-2 -m anthropic/claude-sonnet-4-5
```

## 5. How do we run the reference solution?

Oracle runs `solution/solve.sh` (copies `solution/fixed/*.py` → `/app/relay/`).

Manual:

```bash
export APP_DIR="$(pwd)/environment/repo"
bash solution/solve.sh
PYTHONPATH=environment/repo pytest tests/test_behavior.py
```

## 6. How does the verifier work?

`tests/test.sh` runs `tests/test_behavior.py` and **always** writes `/logs/verifier/reward.txt` (`1` or `0`).

- Ephemeral mock downstream + in-process relay
- Randomized secrets, payloads, idempotency keys
- Behavior contracts (hits, headers, status sequences, backoff gaps)
- Canary file integrity against test tampering

## 7. What edge cases are covered?

| Case | Expectation |
|------|-------------|
| Duplicate `Idempotency-Key` | One downstream hit; second `replayed` |
| Awkward JSON whitespace | Outbound HMAC over **raw** bytes |
| `REQUIRE_SIGNATURE=1` unsigned | HTTP 401, zero downstream hits |
| Downstream HTTP 400 | Single attempt, no retries |
| Downstream 503 body containing `ok` | Still retried until real 2xx |
| Backoff | Gaps increase (~exponential) |
| Failed then same key | Key not consumed on failure |

## 8. What grader exploits did you test?

See [`analysis/grader_attacks.md`](analysis/grader_attacks.md).

## 9. What happened when you ran an AI coding agent?

See [`analysis/model_runs.md`](analysis/model_runs.md). Short version: **oracle 1.0**, **nop 0.0**; Terminus-2 runs hit Anthropic `AuthenticationError` (invalid host API key — environment flaw on credentials, not the task). Cursor authoring agent produced the reference fix and local suite green.

## Starting state vs oracle

| State | Result |
|-------|--------|
| `environment/repo` as shipped / `nop` | fails verifier → reward `0` |
| After `solution/solve.sh` / `oracle` | passes verifier → reward `1` |

## License / originality

All code under `environment/repo` is **original** educational code (MIT). No proprietary or third-party app code.

## Submission notes

Email: `sangamesh@synthiumlabs.tech`  
Subject: `Coding RL Environment Assignment | [Your Name]`  

Include: **full name**, **phone**, **GitHub link**, and the 3–5 line summary at the top of this README.
