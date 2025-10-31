#!/usr/bin/env python3
"""Backup and patch Bambu H2S filament profiles with air filtration keys."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import shutil
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Callable

UPDATE_FILAMENTPROFILE_AIR_EXHAUST50 = True
UPDATE_MACHINEPROFILE_AIR_FILTRATION_SUPPORT = True
UPDATE_MACHINEPROFILE_EXHAUST_AFTER_RUN = True
EXHAUST_AFTER_RUN_SECONDS = 300



SNIPPET = OrderedDict(
    (
        ("activate_air_filtration", ["1"]),
        ("complete_print_exhaust_fan_speed", ["0"]),
        ("during_print_exhaust_fan_speed", ["50"]),
    )
)

if EXHAUST_AFTER_RUN_SECONDS <= 0:
    raise ValueError("EXHAUST_AFTER_RUN_SECONDS must be positive.")

MACHINE_END_GCODE_SNIPPET = (
    "; exhaust after-run",
    "M106 P3 S255",
    f"G4 S{EXHAUST_AFTER_RUN_SECONDS}",
    "M106 P3 S0",
)

DEFAULT_FILAMENTS = (
    "Bambu PLA Basic @BBL H2S.json",
    "Bambu PLA Silk @BBL H2S.json",
    "Bambu PLA Silk+ @BBL H2S.json",
)

DEFAULT_MACHINE_PROFILES = (
    "Bambu Lab H2S 0.2 nozzle.json",
    "Bambu Lab H2S 0.4 nozzle.json",
    "Bambu Lab H2S 0.6 nozzle.json",
    "Bambu Lab H2S 0.8 nozzle.json",
)

SYSTEM_FILAMENT_SUBPATH = ("BambuStudio", "system", "BBL", "Filament")
SYSTEM_MACHINE_SUBPATH = ("BambuStudio", "system", "BBL", "machine")

PatchFunc = Callable[[OrderedDict], tuple[OrderedDict, bool]]


def _build_subpath(root: Path, segments: tuple[str, ...]) -> Path:
    return root.joinpath(*segments)


def _load_profile(path: Path) -> OrderedDict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=OrderedDict)


def _ensure_filtration(data: OrderedDict) -> tuple[OrderedDict, bool]:
    if not UPDATE_FILAMENTPROFILE_AIR_EXHAUST50:
        return data, False
    changed = False
    updated = OrderedDict()

    for key, value in data.items():
        if key in SNIPPET:
            target = SNIPPET[key]
            if value != target:
                updated[key] = target
                changed = True
            else:
                updated[key] = value
        else:
            updated[key] = value

    for key, target in SNIPPET.items():
        if key not in updated:
            updated[key] = target
            changed = True

    return updated, changed


def _ensure_air_filtration_support(data: OrderedDict) -> tuple[OrderedDict, bool]:
    if not UPDATE_MACHINEPROFILE_AIR_FILTRATION_SUPPORT:
        return data, False
    changed = False
    updated = OrderedDict()
    support_key = "support_air_filtration"

    for key, value in data.items():
        if key == support_key:
            if value != "1":
                updated[key] = "1"
                changed = True
            else:
                updated[key] = value
        else:
            updated[key] = value

    if support_key not in updated:
        updated[support_key] = "1"
        changed = True

    return updated, changed


def _contains_subsequence(sequence: list[str], candidate: tuple[str, ...]) -> bool:
    window = len(candidate)
    if window == 0:
        return True
    needle = list(candidate)
    for idx in range(len(sequence) - window + 1):
        if sequence[idx : idx + window] == needle:
            return True
    return False


def _ensure_machine_end_gcode(data: OrderedDict) -> tuple[OrderedDict, bool]:
    if not UPDATE_MACHINEPROFILE_EXHAUST_AFTER_RUN:
        return data, False
    changed = False
    updated = OrderedDict()
    gcode_key = "machine_end_gcode"

    for key, value in data.items():
        if key == gcode_key:
            if isinstance(value, list):
                if _contains_subsequence(value, MACHINE_END_GCODE_SNIPPET):
                    updated[key] = value
                else:
                    updated[key] = value + list(MACHINE_END_GCODE_SNIPPET)
                    changed = True
            else:
                updated[key] = list(MACHINE_END_GCODE_SNIPPET)
                changed = True
        else:
            updated[key] = value

    if gcode_key not in updated:
        updated[gcode_key] = list(MACHINE_END_GCODE_SNIPPET)
        changed = True

    return updated, changed


def _ensure_machine_profile(data: OrderedDict) -> tuple[OrderedDict, bool]:
    if not (UPDATE_MACHINEPROFILE_AIR_FILTRATION_SUPPORT or UPDATE_MACHINEPROFILE_EXHAUST_AFTER_RUN):
        return data, False
    updated_support, support_changed = _ensure_air_filtration_support(data)
    updated_gcode, gcode_changed = _ensure_machine_end_gcode(updated_support)
    return updated_gcode, support_changed or gcode_changed


def _write_profile(path: Path, data: OrderedDict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=4, ensure_ascii=False)
        handle.write("\n")


def _create_backup(path: Path) -> Path:
    timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{path.stem}.{timestamp}_backup{path.suffix}"
    backup_path = path.with_name(backup_name)
    shutil.copy2(path, backup_path)
    return backup_path


def _infer_patcher(path: Path, data: OrderedDict) -> PatchFunc:
    name = path.name.lower()
    if "bambu lab h2s" in name and "nozzle" in name:
        return _ensure_machine_profile
    return _ensure_filtration


def process_file(path: Path, dry_run: bool = False, patcher: PatchFunc | None = None) -> int:
    try:
        profile = _load_profile(path)
    except FileNotFoundError:
        print(f"[error] {path} not found", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"[error] {path}: invalid JSON ({exc})", file=sys.stderr)
        return 1
    selected_patcher = patcher or _infer_patcher(path, profile)
    patched, changed = selected_patcher(profile)
    if not changed:
        print(f"[skip] {path.name} already up to date")
        return 0

    if dry_run:
        backup_path = path.with_name(
            f"{path.stem}.{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_backup{path.suffix}"
        )
        print(f"[dry-run] Would create {backup_path.name} and update {path.name}")
        return 0

    backup_path = _create_backup(path)
    _write_profile(path, patched)
    print(f"[updated] {path.name} (backup: {backup_path.name})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inject air filtration keys into Bambu H2S filament profiles."
    )
    parser.add_argument(
        "json_files",
        nargs="*",
        type=Path,
        help=(
            "Path(s) to the JSON profile(s) to patch. "
            "If omitted, all JSON profiles in "
            "%AppData%/BambuStudio/system/BBL/Filament are used."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the planned backup and write operations without modifying files.",
    )
    return parser


def _collect_default_targets(appdata_root: Path) -> tuple[list[tuple[Path, PatchFunc]], bool]:
    targets: list[tuple[Path, PatchFunc]] = []
    errors = False

    if UPDATE_FILAMENTPROFILE_AIR_EXHAUST50:
        system_dir = _build_subpath(appdata_root, SYSTEM_FILAMENT_SUBPATH)
        if system_dir.is_dir():
            print(f"[info] Using system directory: {system_dir}")
            for filename in DEFAULT_FILAMENTS:
                candidate = system_dir / filename
                if candidate.exists():
                    targets.append((candidate, _ensure_filtration))
                else:
                    errors = True
                    print(f"[error] Expected profile not found: {candidate}", file=sys.stderr)
        else:
            print(f"[error] System directory {system_dir} not found", file=sys.stderr)
            errors = True
    else:
        print("[info] Filament profile update disabled; skipping filament targets.")

    if UPDATE_MACHINEPROFILE_AIR_FILTRATION_SUPPORT or UPDATE_MACHINEPROFILE_EXHAUST_AFTER_RUN:
        machine_dir = _build_subpath(appdata_root, SYSTEM_MACHINE_SUBPATH)
        if machine_dir.is_dir():
            print(f"[info] Using machine directory: {machine_dir}")
            for filename in DEFAULT_MACHINE_PROFILES:
                candidate = machine_dir / filename
                if candidate.exists():
                    targets.append((candidate, _ensure_machine_profile))
                else:
                    errors = True
                    print(f"[error] Expected machine profile not found: {candidate}", file=sys.stderr)
        else:
            print(f"[error] Machine directory {machine_dir} not found", file=sys.stderr)
            errors = True
    else:
        print("[info] Machine profile updates disabled; skipping machine targets.")

    return targets, errors


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    targets: list[tuple[Path, PatchFunc | None]]

    if args.json_files:
        targets = [(candidate, None) for candidate in args.json_files]
    else:
        appdata = os.environ.get("APPDATA")
        if not appdata:
            print("[error] APPDATA environment variable not set", file=sys.stderr)
            return 1
        appdata_root = Path(appdata)
        default_targets, has_errors = _collect_default_targets(appdata_root)
        if has_errors:
            return 1
        targets = default_targets

    status = 0
    for candidate, patcher in targets:
        result = process_file(candidate, dry_run=args.dry_run, patcher=patcher)
        if result != 0:
            status = result
    return status


if __name__ == "__main__":
    raise SystemExit(main())
