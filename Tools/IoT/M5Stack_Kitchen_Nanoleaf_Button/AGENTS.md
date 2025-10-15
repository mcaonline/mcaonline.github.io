# Repository Guidelines

## Project Structure & Module Organization
- `kitchenmove50.py` runs the M5Stack kitchen button automation, bundling configuration (`Config`), time helpers, and hardware orchestration for Shelly, Nanoleaf, and WLED targets.
- `nanoleaf_an_aus_status_fulldebug.py` is a MicroPython debug loop for the Atom S3 Lite button that polls Nanoleaf state and toggles power.
- `nanoleaf_get_apikey.py` is a desktop Python helper for generating Nanoleaf API keys; keep the fetched token out of version control.
- There is no dedicated tests or assets directory; hardware-facing logic lives alongside the scripts, so be deliberate about keeping each file focused on one workflow.

## Build, Test, and Development Commands
- `mpremote run kitchenmove50.py` executes the main automation on a connected M5Stack; use `mpremote mount .` for longer sessions.
- `python nanoleaf_get_apikey.py` (desktop CPython) requests a new Nanoleaf API token.
- `mpremote repl` opens an interactive REPL to watch log output while exercising Test Mode timings.

## Coding Style & Naming Conventions
- Use 4 spaces for indentation, `CamelCase` for classes, and `snake_case` for functions and variables; keep constants uppercase as in `WLED_JSON_EIN`.
- Group configuration in the `Config` class and prefer clear docstrings or one-line comments for non-obvious hardware logic; avoid scattering hard-coded IPs outside this block.
- MicroPython memory is tight—reuse objects where possible and guard network calls with simple retries instead of heavy abstractions.

## Testing Guidelines
- Rely on hardware verification; enable fast iterations with `Config(test_mode=True)` to shorten inactivity windows before deploying production values.
- Capture output with `mpremote repl` or the serial console and confirm PIR triggers, manual overrides, and Nanoleaf/WLED state transitions.
- Record manual test notes (date, device, observed states) in the pull request to document coverage, since no automated suite exists.

## Commit & Pull Request Guidelines
- History favors short imperative messages (`upd`, `del`, `Create ...`); keep that style but append the touched module for clarity, e.g., `upd: tighten PIR window logic`.
- Squash unrelated edits, reference the hardware scenario in the description, and link to any relevant issue or runbook.
- Pull requests should include: purpose summary, hardware setup used, test-mode vs. production-mode checks, and screenshots or serial logs when behavior changes.

## Security & Configuration Tips
- Leave `API_KEY` placeholders empty in source; provision secrets on-device or through environment variables before flashing.
- Double-check IP assignments before committing to avoid publishing internal network details.
