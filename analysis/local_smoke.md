# Local smoke checks (without Harbor)

From repo root on a machine with Python 3.12+:

```bash
# Starting state should fail most behavioral tests
PYTHONPATH=environment/repo python -m pytest tests/test_behavior.py -q

# Apply reference solution
export APP_DIR="$(pwd)/environment/repo"   # Git Bash / WSL
bash solution/solve.sh
PYTHONPATH=environment/repo python -m pytest tests/test_behavior.py -q
# expect: 7 passed
```

On Windows PowerShell, copy fixed modules instead of bash if needed:

```powershell
Copy-Item solution\fixed\*.py environment\repo\relay\ -Force
$env:PYTHONPATH = "$PWD\environment\repo"
python -m pytest tests/test_behavior.py -q
```

Remember to restore the broken files under `environment/repo/relay/` before rebuilding the Docker image (or reset via git).
