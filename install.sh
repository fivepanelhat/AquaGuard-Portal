#!/usr/bin/env bash
# AquaGuard-Portal — dual-platform installer (Linux / macOS)
# One-line: curl -fsSL https://raw.githubusercontent.com/fivepanelhat/AquaGuard-Portal/main/install.sh | bash
# From clone: ./install.sh
set -euo pipefail

REPO_URL="${PORTAL_REPO_URL:-https://github.com/fivepanelhat/AquaGuard-Portal.git}"
INSTALL_DIR="${PORTAL_HOME:-$HOME/.aquaguard-portal-app}"

info() { printf '\033[36m[aquaguard-portal]\033[0m %s\n' "$1"; }
warn() { printf '\033[33m[aquaguard-portal]\033[0m %s\n' "$1"; }
err()  { printf '\033[31m[aquaguard-portal]\033[0m %s\n' "$1" >&2; }

PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  err "Python 3.10+ is required. On Debian/Ubuntu/RPi OS:"
  err "  sudo apt-get install -y python3 python3-venv python3-pip git build-essential"
  exit 1
fi
PY_VER="$("$PYTHON_BIN" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
info "Using Python $PY_VER ($PYTHON_BIN)"
PY_MAJOR="$("$PYTHON_BIN" -c 'import sys; print(sys.version_info[0])')"
PY_MINOR="$("$PYTHON_BIN" -c 'import sys; print(sys.version_info[1])')"
if [[ "$PY_MAJOR" -lt 3 ]] || { [[ "$PY_MAJOR" -eq 3 ]] && [[ "$PY_MINOR" -lt 10 ]]; }; then
  err "Python 3.10+ is required (found ${PY_MAJOR}.${PY_MINOR})."
  exit 1
fi

if [[ -f "bootstrap.py" ]] && [[ -f "requirements.txt" || -f "setup.py" || -f "pyproject.toml" ]]; then
  SRC_DIR="$(pwd)"
  info "Installing from current checkout: $SRC_DIR"
else
  if ! command -v git >/dev/null 2>&1; then
    err "git is required. Install git or run from a clone."
    exit 1
  fi
  mkdir -p "$INSTALL_DIR"
  SRC_DIR="$INSTALL_DIR/src"
  if [[ -d "$SRC_DIR/.git" ]]; then
    info "Updating existing checkout in $SRC_DIR"
    git -C "$SRC_DIR" pull --ff-only || warn "Could not fast-forward; using existing checkout."
  else
    info "Cloning $REPO_URL"
    git clone --depth 1 "$REPO_URL" "$SRC_DIR"
  fi
fi

cd "$SRC_DIR"
info "Running bootstrap.py"
"$PYTHON_BIN" bootstrap.py --portal-only
info "Done. Activate: source $SRC_DIR/venv/bin/activate"
