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
MACHINE_END_GCODE_SNIPPET_LIST = list(MACHINE_END_GCODE_SNIPPET)

DEFAULT_FILAMENTS = (
    "Bambu PLA Basic @base.json",
    "Bambu PLA Silk @base.json",
    "Bambu PLA Silk+ @base.json",
)

DEFAULT_MACHINE_PROFILES = ("Bambu Lab H2S 0.4 nozzle.json",)

SYSTEM_FILAMENT_SUBPATH = ("BambuStudio", "system", "BBL", "Filament")
SYSTEM_MACHINE_SUBPATH = ("BambuStudio", "system", "BBL", "machine")

PatchFunc = Callable[[OrderedDict], tuple[OrderedDict, list[str]]]


def _ensure_directory_backup(source: Path, backup: Path) -> bool:
    if not source.exists():
        print(f"[error] Source directory {source} not found", file=sys.stderr)
        return False
    if backup.exists():
        print(f"[info] Backup directory already present: {backup}")
        return True
    try:
        shutil.copytree(source, backup)
    except OSError as exc:  # pragma: no cover - critical failure, surface to user
        print(f"[error] Failed to create backup {backup} ({exc})", file=sys.stderr)
        return False
    print(f"[info] Created backup directory: {backup}")
    return True


def _build_subpath(root: Path, segments: tuple[str, ...]) -> Path:
    return root.joinpath(*segments)


def _load_profile(path: Path) -> OrderedDict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=OrderedDict)


def _format_value_for_report(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _ensure_filtration(data: OrderedDict) -> tuple[OrderedDict, list[str]]:
    if not UPDATE_FILAMENTPROFILE_AIR_EXHAUST50:
        return data, []
    updated = OrderedDict()
    changes: list[str] = []

    for key, value in data.items():
        if key in SNIPPET:
            target = SNIPPET[key]
            if value != target:
                updated[key] = target
                changes.append(
                    f"{key}: set to {_format_value_for_report(target)} (was {_format_value_for_report(value)})"
                )
            else:
                updated[key] = value
        else:
            updated[key] = value

    for key, target in SNIPPET.items():
        if key not in updated:
            updated[key] = target
            changes.append(f"{key}: added {_format_value_for_report(target)}")

    return updated, changes


def _ensure_air_filtration_support(
    data: OrderedDict, *, source_path: Path | None = None
) -> tuple[OrderedDict, list[str]]:
    if not UPDATE_MACHINEPROFILE_AIR_FILTRATION_SUPPORT:
        return data, []
    updated = OrderedDict()
    changes: list[str] = []
    support_key = "support_air_filtration"
    inherits_value = data.get("inherits")
    inherits_local = (
        isinstance(inherits_value, str)
        and "bambu lab h2s" in inherits_value.lower()
        and "nozzle" in inherits_value.lower()
    )
    inherited_support = None
    if support_key not in data:
        inherited_support = _inherit_machine_value_from_parent(support_key, data, source_path)

    for key, value in data.items():
        if key == support_key:
            if value != "1":
                updated[key] = "1"
                changes.append(
                    f"{support_key}: set to \"1\" (was {_format_value_for_report(value)})"
                )
            else:
                updated[key] = value
        else:
            updated[key] = value

    if support_key not in updated:
        if inherits_local and inherited_support == "1":
            return updated, changes
        updated[support_key] = "1"
        changes.append(f"{support_key}: added \"1\"")

    return updated, changes


def _contains_subsequence(sequence: list[str], candidate: tuple[str, ...]) -> bool:
    window = len(candidate)
    if window == 0:
        return True
    needle = list(candidate)
    for idx in range(len(sequence) - window + 1):
        if sequence[idx : idx + window] == needle:
            return True
    return False


def _append_snippet_to_string(text: str) -> tuple[str, bool]:
    lines = text.splitlines()
    newline = "\r\n" if "\r\n" in text else "\n"
    had_trailing_newline = text.endswith(("\n", "\r"))
    if _contains_subsequence(lines, MACHINE_END_GCODE_SNIPPET):
        return text, False

    updated_lines = list(lines)
    updated_lines.extend(MACHINE_END_GCODE_SNIPPET)
    new_text = newline.join(updated_lines)
    if had_trailing_newline:
        new_text += newline
    return new_text, True


def _append_machine_end_gcode(value: object) -> tuple[object, bool]:
    if isinstance(value, list):
        if _contains_subsequence(value, MACHINE_END_GCODE_SNIPPET):
            return value, False
        return value + MACHINE_END_GCODE_SNIPPET_LIST, True
    if isinstance(value, str):
        return _append_snippet_to_string(value)
    if value is None:
        return _append_snippet_to_string("")
    return _append_snippet_to_string(str(value))


def _collect_parent_hints(data: OrderedDict) -> list[str]:
    hints: list[str] = []
    markers = ("parent", "inherit")

    def _walk(node: object, key_path: str = "") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                path = f"{key_path}.{key}" if key_path else key
                _walk(value, path)
        elif isinstance(node, list):
            for item in node:
                _walk(item, key_path)
        elif isinstance(node, str):
            if not key_path:
                return
            lowered = key_path.lower()
            if any(marker in lowered for marker in markers):
                hints.append(node)

    _walk(data)
    return hints


def _resolve_parent_paths(hints: list[str], source_path: Path | None) -> list[Path]:
    if source_path is None:
        return []
    parent_dir = source_path.parent
    resolved: list[Path] = []
    seen: set[Path] = set()

    for hint in hints:
        candidates = [hint]
        if not hint.lower().endswith(".json"):
            candidates.append(f"{hint}.json")
        for candidate in candidates:
            candidate_path = Path(candidate)
            if not candidate_path.is_absolute():
                candidate_path = (parent_dir / candidate_path).resolve()
            else:
                candidate_path = candidate_path.resolve()
            if (
                candidate_path.exists()
                and candidate_path not in seen
                and candidate_path != source_path.resolve()
            ):
                resolved.append(candidate_path)
                seen.add(candidate_path)

    return resolved


def _inherit_machine_value_from_parent(
    key: str, data: OrderedDict, source_path: Path | None, visited: set[Path] | None = None
) -> object | None:
    if source_path is None:
        return None
    if visited is None:
        visited = set()
    try:
        current_path = source_path.resolve()
    except FileNotFoundError:
        current_path = source_path
    if current_path in visited:
        return None
    visited.add(current_path)

    hints = _collect_parent_hints(data)
    for candidate in _resolve_parent_paths(hints, source_path):
        resolved_candidate = candidate.resolve()
        if resolved_candidate in visited:
            continue
        try:
            parent_data = _load_profile(candidate)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
        parent_value = parent_data.get(key)
        if parent_value is not None:
            return parent_value
        inherited = _inherit_machine_value_from_parent(key, parent_data, candidate, visited)
        if inherited is not None:
            return inherited
    return None


def _ensure_machine_end_gcode(
    data: OrderedDict, *, source_path: Path | None = None
) -> tuple[OrderedDict, list[str]]:
    if not UPDATE_MACHINEPROFILE_EXHAUST_AFTER_RUN:
        return data, []
    updated = OrderedDict()
    changes: list[str] = []
    gcode_key = "machine_end_gcode"
    gcode_present = False

    for key, value in data.items():
        if key == gcode_key:
            gcode_present = True
            updated_value, value_changed = _append_machine_end_gcode(value)
            updated[key] = updated_value
            if value_changed:
                changes.append(
                    f"{gcode_key}: appended {json.dumps(MACHINE_END_GCODE_SNIPPET_LIST, ensure_ascii=False)}"
                )
        else:
            updated[key] = value

    if not gcode_present:
        inherited_value = _inherit_machine_value_from_parent(gcode_key, data, source_path)
        if inherited_value is None:
            if source_path:
                print(
                    f"[warn] {source_path.name}: machine_end_gcode not found and parent could not be resolved; skipping append",
                    file=sys.stderr,
                )
            return updated, changes
        appended_value, appended_changed = _append_machine_end_gcode(inherited_value)
        if appended_changed:
            updated[gcode_key] = appended_value
            changes.append(
                f"{gcode_key}: appended {json.dumps(MACHINE_END_GCODE_SNIPPET_LIST, ensure_ascii=False)}"
            )

    return updated, changes


def _ensure_machine_profile(
    data: OrderedDict, *, source_path: Path | None = None
) -> tuple[OrderedDict, list[str]]:
    if not (UPDATE_MACHINEPROFILE_AIR_FILTRATION_SUPPORT or UPDATE_MACHINEPROFILE_EXHAUST_AFTER_RUN):
        return data, []
    updated_support, support_changes = _ensure_air_filtration_support(
        data, source_path=source_path
    )
    updated_gcode, gcode_changes = _ensure_machine_end_gcode(
        updated_support, source_path=source_path
    )
    return updated_gcode, support_changes + gcode_changes


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


def _ensure_default_backups(appdata_root: Path) -> bool:
    success = True
    if UPDATE_FILAMENTPROFILE_AIR_EXHAUST50:
        filament_dir = _build_subpath(appdata_root, SYSTEM_FILAMENT_SUBPATH)
        filament_backup = filament_dir.parent / f"{filament_dir.name.lower()}_backup"
        success = _ensure_directory_backup(filament_dir, filament_backup) and success
    if UPDATE_MACHINEPROFILE_AIR_FILTRATION_SUPPORT or UPDATE_MACHINEPROFILE_EXHAUST_AFTER_RUN:
        machine_dir = _build_subpath(appdata_root, SYSTEM_MACHINE_SUBPATH)
        machine_backup = machine_dir.parent / f"{machine_dir.name.lower()}_backup"
        success = _ensure_directory_backup(machine_dir, machine_backup) and success
    return success


def _infer_patcher(path: Path, data: OrderedDict) -> PatchFunc:
    lower_name = path.name.lower()
    machine_indicators = ("machine_end_gcode", "support_air_filtration")
    if any(key in data for key in machine_indicators) or "nozzle" in lower_name or path.parent.name.lower() == "machine":
        return lambda payload, target_path=path: _ensure_machine_profile(payload, source_path=target_path)
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
    patched, change_details = selected_patcher(profile)
    if not change_details:
        print(f"[skip] {path.name} already up to date")
        return 0

    if dry_run:
        backup_path = path.with_name(
            f"{path.stem}.{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_backup{path.suffix}"
        )
        print(f"[dry-run] Would create {backup_path.name} and update {path.name}")
        for detail in change_details:
            print(f"         - {detail}")
        return 0

    backup_path = _create_backup(path)
    _write_profile(path, patched)
    print(f"[updated] {path.name} (backup: {backup_path.name})")
    for detail in change_details:
        print(f"         - {detail}")
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
                    targets.append(
                        (
                            candidate,
                            lambda payload, target_path=candidate: _ensure_machine_profile(
                                payload, source_path=target_path
                            ),
                        )
                    )
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
        if not _ensure_default_backups(appdata_root):
            return 1
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
