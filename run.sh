#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
ENTRYPOINT="$ROOT_DIR/main.py"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Virtualenv not found at $ROOT_DIR/.venv"
  echo "Create it first with:"
  echo "  python3 -m venv .venv"
  echo "  source .venv/bin/activate"
  echo "  pip install -r requirements.txt"
  echo "  pip install -e ."
  exit 1
fi

command="${1:-run}"
shift || true

case "$command" in
  run)
    exec "$VENV_PYTHON" "$ENTRYPOINT" --debug "$@"
    ;;
  learn)
    target="${1:-}"
    if [[ "$target" != "copy" && "$target" != "paste" ]]; then
      echo "Usage: ./run.sh learn copy|paste"
      exit 1
    fi
    shift
    exec "$VENV_PYTHON" "$ENTRYPOINT" --learn "$target" "$@"
    ;;
  feedback)
    exec "$VENV_PYTHON" "$ENTRYPOINT" --debug --feedback "$@"
    ;;
  help|-h|--help)
    cat <<'EOF'
Usage:
  ./run.sh run
  ./run.sh learn copy
  ./run.sh learn paste
  ./run.sh feedback

Commands:
  run       Start normal detection with --debug
  learn     Record new training samples for copy or paste
  feedback  Start detection with interactive reinforcement enabled
EOF
    ;;
  *)
    echo "Unknown command: $command"
    echo "Try: ./run.sh help"
    exit 1
    ;;
esac
