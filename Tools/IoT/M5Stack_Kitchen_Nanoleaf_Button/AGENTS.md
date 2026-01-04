# Repository Guidelines

## Project Structure & Module Organization
- `kitchenmove52.py` runs the M5Stack kitchen button automation, bundling configuration (`Config`), time helpers (`TimeUtils`), and orchestration for Shelly/WLED with PIR + button handling.
- `nanoleaf_an_aus_status_fulldebug.py` is a MicroPython debug loop for the Atom S3 Lite button that polls Nanoleaf state and toggles power.
- `nanoleaf_get_apikey.py` is a desktop Python helper for generating Nanoleaf API keys; keep the fetched token out of version control.
- There is no dedicated tests or assets directory; hardware-facing logic lives alongside the scripts, so keep each file focused on one workflow.

## Implemented Features (kitchenmove52.py)
- Configuration profiles for test vs. production (timeouts, PIR thresholds, manual override window, auto-on cutoff).
- German local time + DST handling (`TimeUtils`) with NTP sync at boot and every 12 hours.
- Sunset table by month for auto-on gating (`DarknessChecker`), with a hard cutoff after `AUTO_ON_NICHT_NACH`.
- Manual override timer to ignore PIR after manual toggles.
- PIR sliding-window event aggregation with debounce + threshold-based auto-on.
- Inactivity-based auto-off timer (`INAKT_TIMEOUT`).
- Button handling: long-press toggles main lights, short press toggles WLED, double-click toggles test-mode override.
- WLED control with auto-off timer and status LED feedback.
- Shelly relay control for main lights with status LED feedback.
- Status LED controller with display duration, overrides, and blinking during network calls.
- Hardware watchdog feed loop with boot diagnostics, memory logging, and periodic GC.
- Wi-Fi monitor with reconnect attempts and watchdog-safe waits.

## Build, Test, and Development Commands
- `mpremote run kitchenmove52.py` executes the main automation on a connected M5Stack; use `mpremote mount .` for longer sessions.
- `python nanoleaf_get_apikey.py` (desktop CPython) requests a new Nanoleaf API token.
- `mpremote repl` opens an interactive REPL to watch log output while exercising Test Mode timings.

## Coding Style & Naming Conventions
- Use 4 spaces for indentation, `CamelCase` for classes, and `snake_case` for functions and variables; keep constants uppercase as in `WLED_JSON_EIN`.
- Group configuration in the `Config` class and prefer clear docstrings or one-line comments for non-obvious hardware logic; avoid scattering hard-coded IPs outside this block.
- MicroPython memory is tight—reuse objects where possible and guard network calls with simple retries instead of heavy abstractions.

## Testing Guidelines
- Rely on hardware verification; enable fast iterations with `Config(test_mode=True)` to shorten inactivity windows before deploying production values.
- Capture output with `mpremote repl` or the serial console and confirm PIR triggers, manual overrides, and Shelly/WLED state transitions.
- Record manual test notes (date, device, observed states) in the pull request to document coverage, since no automated suite exists.

## Commit & Pull Request Guidelines
- History favors short imperative messages (`upd`, `del`, `Create ...`); keep that style but append the touched module for clarity, e.g., `upd: tighten PIR window logic`.
- Squash unrelated edits, reference the hardware scenario in the description, and link to any relevant issue or runbook.
- Pull requests should include: purpose summary, hardware setup used, test-mode vs. production-mode checks, and screenshots or serial logs when behavior changes.

## Security & Configuration Tips
- Leave `API_KEY` placeholders empty in source; provision secrets via `.env` on-device or through environment variables before flashing.
- Double-check IP assignments before committing to avoid publishing internal network details.

## Nanoleaf Integration (Temporarily Disabled)
- All Nanoleaf API instantiation and control calls in `kitchenmove52.py` are commented out (see `LightStateCache`, `MainLightController`, and `KitchenLightOrchestrator`) so only the Shelly relay governs room lighting.
- Cache refresh logs now report Nanoleaf as disabled, preserving the call sites for a future rollback while preventing failed API lookups for missing keys.

## Runtime Behavior Notes
- Auto-on is gated by `DarknessChecker` (sunset table + `AUTO_ON_NICHT_NACH` cutoff), but auto-off uses the inactivity timer only (`TimerManager.INAKT_TIMEOUT`).
- After a reboot, the cached light state starts as off and the inactivity timer is unset until a PIR event arrives; keep this in mind when diagnosing auto-off behavior.
- Sliding window PIR logic: each motion event prunes any older than `PIR_WINDOW`, appends the new event, and checks `EVENT_THRESHOLD`; reaching the threshold turns on lights and clears the event list.
- Example A (test mode: `EVENT_THRESHOLD=5`, `PIR_WINDOW=60s`): motion at t=0, 10, 20, 30, 40 -> count reaches 5 within 60s, lights turn on, events cleared.
- Example B (test mode): motion at t=0, 25, 50, 70 -> at t=70 the t=0 event drops (older than 60s), count stays at 3; motion at t=90 drops t=25, count stays at 3, no auto-on.
- Debounce prevents triggers within 100 ms, and a periodic cleanup removes stale events even without new motion.
- `DNSCache` and `CircuitBreaker` helpers exist but are not wired into the main flow yet.
