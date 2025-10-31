# Repository Guidelines

## Project Structure & Module Organization
Snapshots appear beside this document as timestamped folders such as `20251031_130820`. Each snapshot contains `Original` (reference) and `Modifiziert` (editable) profiles for Bambu H2S materials. Never alter `Original`; stage all adjustments inside `Modifiziert`. Legacy baselines sit under `older/`, grouped by Bambu Studio release. `Anleitung.txt` records manual override targets, and `script_add_arifilterto_pla.cmd` is the sole automation entry point.

## Build, Test, and Development Commands
Run only the provided `.cmd` helper. From a Windows Command Prompt, call `script_add_arifilterto_pla.cmd`. The script creates the next timestamped folder, scaffolds `Original`/`Modifiziert`, copies the three system profiles from `%AppData%\BambuStudio\system\BBL\Filament\`, and injects the filtration snippet. It halts if any source file is missing so you can reinstall or export the profile. Rerun the command after fixes; it always refreshes the latest snapshot.

## Coding Style & Naming Conventions
Keep JSON indented with four spaces, preserve existing key ordering, and append new entries immediately before the closing block they relate to. Filtration keys must render exactly as:
```json
    "activate_air_filtration": [
        "1"
    ],
    "complete_print_exhaust_fan_speed": [
        "0"
    ],
    "during_print_exhaust_fan_speed": [
        "50"
    ],
```
Name new profiles following `Bambu <Material> <Variant> @BBL H2S.json`, for example `Bambu PLA-CF Natural @BBL H2S.json`.

## Testing Guidelines
Load patched profiles into Bambu Studio via `%AppData%\BambuStudio\user\<ID>\Filament`. Confirm the UI exposes the three filtration settings for every updated material. When machine presets shift, mirror the same changes under the hardware paths listed in `Anleitung.txt`. Capture validation screenshots or re-exported profiles to document successful propagation.

## Commit & Pull Request Guidelines
Adopt Conventional Commit prefixes (`feat:`, `fix:`, `docs:`) and keep each commit focused on one snapshot or script tweak. Reference the active Bambu Studio build, the timestamped folder touched, and any supporting artifacts. Pull requests should include a short scenario recap, a link to the comparison directory, and the verification evidence. Update `Anleitung.txt` whenever deployment paths or machine flags evolve.

## Security & Configuration Tips
Run the automation from an account that can read `%AppData%` and write beside this repository so permissions mirror manual exports. Avoid manual edits to `Original` to retain a clean rollback point, and keep local antivirus from quarantining the generated `.json` files or the helper script.
