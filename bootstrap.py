#!/usr/bin/env python3
"""Coastal Alpine Tech — Cross-Platform Bootstrap (Core pin v0.5.10)."""
from __future__ import annotations

import os
import platform
import shlex
import shutil
import subprocess
import sys
import venv

VENV_DIR = "venv"
ROOT_VENV_DIR = ".venv"
PORTALS = ["AquaGuard-Portal", "Blue-Moon-Portal", "SoilGuard-Portal", "Sting-Operation-AI", "Weaver"]
CORE_PACKAGE = "coastal_alpine_core"
CORE_GIT_URL = "https://github.com/fivepanelhat/Coastal-Alpine-Core.git@v0.5.10"


def is_windows() -> bool:
    return sys.platform == "win32"


def require_python_310() -> None:
    if sys.version_info < (3, 10):
        print(f"✗ Python 3.10+ required (found {sys.version.split()[0]})")
        sys.exit(1)


def get_pip_exe(venv_path: str) -> str:
    return os.path.join(venv_path, "Scripts", "pip.exe") if is_windows() else os.path.join(venv_path, "bin", "pip")


def get_python_exe(venv_path: str) -> str:
    return os.path.join(venv_path, "Scripts", "python.exe") if is_windows() else os.path.join(venv_path, "bin", "python")


def get_activate_cmd(venv_path: str) -> str:
    return f".\\{venv_path}\\Scripts\\Activate.ps1" if is_windows() else f"source {venv_path}/bin/activate"


def run_cmd(cmd, description=None, critical: bool = True) -> bool:
    if description:
        print(f"  → {description}")
    try:
        args = cmd if isinstance(cmd, list) else shlex.split(cmd)
        subprocess.run(args, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Command failed: {args if isinstance(cmd, list) else cmd}")
        if e.stderr:
            for line in e.stderr.strip().split("\n")[-12:]:
                print(f"    {line}")
        if critical:
            sys.exit(1)
        return False


def create_venv(venv_path: str) -> bool:
    if os.path.exists(venv_path):
        print(f"  ✓ Virtual environment '{venv_path}' already exists")
        return True
    try:
        try:
            venv.create(venv_path, with_pip=True, upgrade_deps=True)
        except TypeError:
            venv.create(venv_path, with_pip=True)
        except Exception:
            if os.path.exists(venv_path):
                shutil.rmtree(venv_path, ignore_errors=True)
            venv.create(venv_path, with_pip=True)
        print("  ✓ Virtual environment created")
        return True
    except Exception as e:
        print(f"  ✗ Failed to create venv: {e}")
        return False


def install_core(pip_exe: str, editable: bool = False) -> bool:
    if editable and os.path.exists(CORE_PACKAGE):
        return run_cmd([pip_exe, "install", "-e", f"./{CORE_PACKAGE}"], "Installing coastal_alpine_core (editable)")
    ok = run_cmd([pip_exe, "install", f"git+{CORE_GIT_URL}"], f"Installing Core ({CORE_GIT_URL})", critical=False)
    if ok:
        return True
    return run_cmd([pip_exe, "install", "git+https://github.com/fivepanelhat/Coastal-Alpine-Core.git"], "Installing Core (main)")


def setup_portal() -> None:
    venv_path = VENV_DIR
    print(f"\n  Platform: {platform.system()}  Python: {sys.version.split()[0]}")
    if not create_venv(venv_path):
        sys.exit(1)
    pip_exe = get_pip_exe(venv_path)
    py_exe = get_python_exe(venv_path)
    run_cmd([pip_exe, "install", "--upgrade", "pip"], "Upgrading pip")
    install_core(pip_exe, editable=False)
    if os.path.exists("requirements.txt"):
        run_cmd([pip_exe, "install", "-r", "requirements.txt"], "Installing requirements.txt")
    if os.path.exists(".env.example") and not os.path.exists(".env"):
        shutil.copy2(".env.example", ".env")
    run_cmd([py_exe, "-c", "import coastal_alpine_core; print('OK', getattr(coastal_alpine_core,'__version__',''))"], "Verify import")
    print(f"\n  Activate: {get_activate_cmd(venv_path)}\n")


def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)
    require_python_310()
    setup_portal()


if __name__ == "__main__":
    main()
