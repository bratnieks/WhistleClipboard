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

child_pid=""

forward_signal() {
  local signal="$1"
  if [[ -n "$child_pid" ]] && kill -0 "$child_pid" 2>/dev/null; then
    kill "-$signal" "$child_pid" 2>/dev/null || true
  fi
}

wait_for_child() {
  set +e
  wait "$child_pid"
  local exit_code=$?
  set -e
  return "$exit_code"
}

run_python() {
  "$VENV_PYTHON" "$ENTRYPOINT" "$@" &
  child_pid=$!

  trap 'forward_signal INT' INT
  trap 'forward_signal TERM' TERM

  wait_for_child
}

case "$command" in
  run)
    run_python "$@"
    ;;
  debug)
    run_python --debug "$@"
    ;;
  learn)
    target="${1:-}"
    if [[ "$target" != "copy" && "$target" != "paste" ]]; then
      echo "Usage: ./run.sh learn copy|paste"
      exit 1
    fi
    shift
    run_python --learn "$target" "$@"
    ;;
  feedback)
    run_python --debug --feedback "$@"
    ;;
  help|-h|--help)
    cat <<'EOF'
Usage:
  ./run.sh run
  ./run.sh debug
  ./run.sh learn copy
  ./run.sh learn paste
  ./run.sh feedback

Commands:
  run       Start normal detection
  debug     Start detection with --debug enabled
  learn     Record new training samples for copy or paste
  feedback  Start detection with --debug and interactive reinforcement enabled
EOF
    ;;
  *)
    echo "Unknown command: $command"
    echo "Try: ./run.sh help"
    exit 1
    ;;
esac
