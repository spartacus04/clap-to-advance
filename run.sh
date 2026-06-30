#!/usr/bin/env bash
#
# Starts ydotoold, activates the Python virtualenv (if present), and
# runs snap_advance.py. On Ctrl+C (or any exit), stops ydotoold too.

set -u

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="${VENV_DIR:-venv}"
YDOTOOLD_PID=""

# Use a fixed, predictable socket path/perms so the ydotool client
# (run without sudo) can always reach the daemon (run with sudo).
export YDOTOOL_SOCKET="${YDOTOOL_SOCKET:-/run/user/$(id -u)/.ydotool_socket}"

cleanup() {
    echo
    echo "Stopping..."
    if [[ -n "$YDOTOOLD_PID" ]] && kill -0 "$YDOTOOLD_PID" 2>/dev/null; then
        echo "Stopping ydotoold (pid $YDOTOOLD_PID)..."
        kill "$YDOTOOLD_PID" 2>/dev/null
        wait "$YDOTOOLD_PID" 2>/dev/null
    fi
    exit 0
}
trap cleanup INT TERM EXIT

# --- Start ydotoold if it's not already running -----------------------------
if pgrep -x ydotoold >/dev/null; then
    echo "ydotoold already running, leaving it as-is."
else
    if ! command -v ydotoold >/dev/null 2>&1; then
        echo "ERROR: ydotoold not found. Install ydotool first (e.g. sudo pacman -S ydotool)." >&2
        exit 1
    fi
    echo "Starting ydotoold..."
    sudo ydotoold --socket-path="$YDOTOOL_SOCKET" --socket-perm=0666 &
    YDOTOOLD_PID=$!
    sleep 0.5
    if [[ ! -S "$YDOTOOL_SOCKET" ]]; then
        echo "ERROR: ydotoold did not create socket at $YDOTOOL_SOCKET" >&2
        exit 1
    fi
fi

# --- Activate virtualenv if present ------------------------------------------
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    echo "Activating virtualenv ($VENV_DIR)..."
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
else
    echo "No virtualenv found at $VENV_DIR, using system Python."
fi

# --- Run the listener ---------------------------------------------------------
echo "Starting main.py..."
python3 main.py