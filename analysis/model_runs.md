# Model / agent runs

## Environment

- Harbor + Docker Desktop (Windows host, Linux containers)
- Task path: repository root (`harbor run -p .`)

## Run A — Oracle (reference solution)

| Field | Value |
|-------|-------|
| Agent | `oracle` |
| Model | n/a (runs `solution/solve.sh`) |
| Jobs | `jobs/2026-09-04__23-17-01`, reconfirmed `jobs/2026-09-04__23-26-49` |
| Pass/fail | **PASS** (reward **1.0**) |
| Exceptions | 0 |

**Approach:** Oracle copies `solution/fixed/{store,crypto,deliver,server}.py` into `/app/relay/`, then the verifier runs.

**Where it succeeded:** All behavioral contracts (idempotency, HMAC, inbound auth, retries, backoff, canary).

**Why this matters:** Demonstrates the task is solvable and the grader accepts a correct implementation.

## Run B — Nop (no edits)

| Field | Value |
|-------|-------|
| Agent | `nop` |
| Model | n/a |
| Job | `jobs/2026-09-04__23-18-15` |
| Pass/fail | **FAIL** (reward **0.0**) |
| Exceptions | 0 |

**Approach:** Agent makes no changes; starting broken repo is graded as-is.

**Where it failed:** Duplicate deliveries, wrong signature header/body, missing inbound 401, retries on 400 / false success on 503+`ok`, flat backoff.

**Interpretation:** Failure is due to the **planted bugs**, not environment infra. Starting state → fail, oracle → pass satisfies Synthium’s solvability condition.

## Run C — Terminus-2 + Claude Sonnet 4.5 (initial)

| Field | Value |
|-------|-------|
| Agent | `terminus-2` |
| Model | `anthropic/claude-sonnet-4-5` |
| Job | `jobs/2026-09-04__23-19-00` |
| Pass/fail | **Did not complete** |
| Exceptions | `AuthenticationError` (1) |

**What happened:** LiteLLM/Anthropic rejected the configured key (`authentication_error`).

**Model vs environment:** **Host credential problem**, not a task/grader flaw.

## Run D — Terminus-2 + GPT-4.1

| Field | Value |
|-------|-------|
| Agent | `terminus-2` |
| Model | `openai/gpt-4.1` |
| Job | `jobs/2026-09-04__23-20-11` |
| Pass/fail | **Did not complete** |
| Exceptions | `AuthenticationError` (1) |

## Run E — Terminus-2 retries (2026-09-05)

| Field | Value |
|-------|-------|
| Agent | `terminus-2` |
| Model | `anthropic/claude-sonnet-4-5` |
| Jobs | `jobs/2026-09-05__17-58-34`, `jobs/2026-09-05__18-19-37` |
| Pass/fail | **Did not complete** |
| Exceptions | `AuthenticationError` (1 each) |

**What happened:** Harbor started the trial (“running agent…”) then Anthropic returned invalid API key again. Docker was fine on the later attempt.

**Why it failed:** Invalid/revoked Anthropic API key on the host (not agent reasoning, not the RL environment).

**Follow-up for reviewers with a valid key:**

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."  # valid key from console.anthropic.com
harbor run -p . -a terminus-2 -m anthropic/claude-sonnet-4-5
```

## Run F — Cursor coding agent (authoring session)

| Field | Value |
|-------|-------|
| Agent | Cursor Composer |
| Pass/fail | **PASS** on local behavioral suite after applying reference fixes |

**Approach:** Read contracts → inspect `relay/{store,crypto,deliver,server}.py` → multi-file fix → `pytest` 7/7 after fix; 5+ failures on broken start.

**Where a weaker agent might fail:** Fixing only one module; signing re-serialized JSON; treating body text as HTTP success; poisoning idempotency keys on failure.

## Run G — Claude Code via Harbor

| Field | Value |
|-------|-------|
| Agent | `claude-code` |
| Pass/fail | Not completed (`claude auth status` → logged out) |

## Summary

| Agent | Outcome |
|-------|---------|
| oracle | **reward 1.0** |
| nop | **reward 0.0** |
| terminus-2 | Auth error (host API key) — optional section 8 incomplete without valid key |
| Cursor authoring agent | Reference fix + green local suite |

Oracle/nop already answer Synthium’s core solvability question. Section 8 remains optional when no working coding-agent API access is available.
