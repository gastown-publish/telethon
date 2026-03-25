#!/usr/bin/env bash
# Run before git push: credential scan + offline pytest.
# Does not need Telegram credentials or network (except pip on first run).

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -x .venv/bin/python ]]; then
  PYTHON="${ROOT}/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

"${PYTHON}" -m pip install -q -e ".[dev]"
"${PYTHON}" scripts/scan_credentials.py
"${PYTHON}" -m pytest tests/ -q

echo "ci.sh: OK"
