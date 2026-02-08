#!/usr/bin/env python3
"""
Build-time sync script.

Reads constants from backend/src/domain/app_constants.py (the SSoT)
and stamps them into frontend config files that cannot import Python.

Usage:
    python sync_constants.py          # write updates
    python sync_constants.py --check  # CI gate: exit 1 if anything is stale
"""

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Import SSoT constants
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))
from src.domain.app_constants import (
    APP_NAME,
    APP_VERSION,
    APP_IDENTIFIER,
    BACKEND_PORT,
    FRONTEND_DEV_PORT,
)

CHECK_MODE = "--check" in sys.argv
dirty_files: list[str] = []


def _update_json(path: Path, updates: dict[str, object]) -> None:
    """Patch top-level keys in a JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for key, value in updates.items():
        if data.get(key) != value:
            data[key] = value
            changed = True
    if changed:
        if CHECK_MODE:
            dirty_files.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(f"  updated {path.relative_to(ROOT)}")


def _update_nested_json(path: Path, pointer: list[str], value: object) -> None:
    """Patch a nested key (e.g. ["app","windows",0,"title"]) in a JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    node = data
    for segment in pointer[:-1]:
        node = node[int(segment)] if isinstance(node, list) else node[segment]
    final_key = pointer[-1]
    if isinstance(node, list):
        final_key = int(final_key)
    if node[final_key] != value:
        node[final_key] = value
        if CHECK_MODE:
            dirty_files.append(f"{path.relative_to(ROOT)}  [{'/'.join(map(str, pointer))}]")
        else:
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(f"  updated {path.relative_to(ROOT)} [{'/'.join(map(str, pointer))}]")


def _regex_replace(path: Path, pattern: str, replacement: str, count: int = 0) -> None:
    """Replace a regex match in a text file."""
    text = path.read_text(encoding="utf-8")
    new_text = re.sub(pattern, replacement, text, count=count)
    if text != new_text:
        if CHECK_MODE:
            dirty_files.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(new_text, encoding="utf-8")
            print(f"  updated {path.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# 2. Sync targets
# ---------------------------------------------------------------------------
print("sync_constants: reading from app_constants.py")
print(f"  APP_NAME={APP_NAME}  APP_VERSION={APP_VERSION}  APP_IDENTIFIER={APP_IDENTIFIER}")
print(f"  BACKEND_PORT={BACKEND_PORT}  FRONTEND_DEV_PORT={FRONTEND_DEV_PORT}")
print()

# --- frontend/package.json ---
pkg = ROOT / "frontend" / "package.json"
_update_json(pkg, {"version": APP_VERSION})

# --- frontend/src-tauri/tauri.conf.json ---
tauri = ROOT / "frontend" / "src-tauri" / "tauri.conf.json"
_update_json(tauri, {
    "productName": APP_NAME,
    "version": APP_VERSION,
    "identifier": APP_IDENTIFIER,
})
_update_nested_json(tauri, ["app", "windows", "0", "title"], APP_NAME)
_update_nested_json(tauri, ["build", "devUrl"], f"http://localhost:{FRONTEND_DEV_PORT}")

# --- frontend/src-tauri/Cargo.toml ---
cargo = ROOT / "frontend" / "src-tauri" / "Cargo.toml"
_regex_replace(cargo, r'^version\s*=\s*".*?"', f'version = "{APP_VERSION}"')

# --- frontend/vite.config.ts ---
vite = ROOT / "frontend" / "vite.config.ts"
# Only replace the first port: (server port), not HMR port
_regex_replace(vite, r'port:\s*\d+', f'port: {FRONTEND_DEV_PORT}', count=1)

# --- frontend/src/api/client.ts ---
client = ROOT / "frontend" / "src" / "api" / "client.ts"
_regex_replace(
    client,
    r'const API_BASE\s*=\s*"http://localhost:\d+"',
    f'const API_BASE = "http://localhost:{BACKEND_PORT}"',
)

# ---------------------------------------------------------------------------
# 3. Report
# ---------------------------------------------------------------------------
if CHECK_MODE:
    if dirty_files:
        print("ERROR: The following files are out of sync with app_constants.py:")
        for f in dirty_files:
            print(f"  - {f}")
        print("\nRun `python sync_constants.py` to fix them.")
        sys.exit(1)
    else:
        print("All config files are in sync.")
        sys.exit(0)
else:
    print("\nDone.")
