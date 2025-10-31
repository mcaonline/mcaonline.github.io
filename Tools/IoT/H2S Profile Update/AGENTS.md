# Repository Guidelines

## Project Structure & Module Organization
The repository stores time-stamped snapshot folders (for example `20251031_130820`), each containing paired `Original` and `Modifiziert` profiles for Bambu H2S materials. Treat `Original` as the pristine reference and restrict edits to `Modifiziert`. Legacy baselines live under `older/`, grouped by Bambu Studio release. `Anleitung.txt` documents manual override paths, and `script_add_arifilterto_pla.cmd` automates profile export and patching.

## Build, Test, and Development Commands
Execute the automation. It creates a timestamped folder beside the script, scaffolds `Original` and `Modifiziert`, so the snapshot uses the same permissions as manually created directories. It copies the three system filament profiles from `%AppData%\BambuStudio\system\BBL\Filament\`, halts with a message if any file is missing, and injects the `activate_air_filtration`, `complete_print_exhaust_fan_speed`, and `during_print_exhaust_fan_speed` entries into each file in `Modifiziert`. Ensure the snippet lands as clean JSON, for example:
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
Reindent the helper's two-space block to four before committing.

## Coding Style & Naming Conventions
Keep four-space indentation in JSON and preserve the existing key order to minimise noisy diffs. New filenames should follow `Bambu <Material> <Variant> @BBL H2S.json`. 

## Testing Guidelines
Before publishing, load the modified profiles into Bambu Studio via `%AppData%\BambuStudio\user\<ID>\Filament` and confirm the H2S filtration settings surface in the filament UI. When printer configs change, mirror them under the machine paths listed in `Anleitung.txt`. Capture screenshots or export profiles to show that `activate_air_filtration`, `complete_print_exhaust_fan_speed`, and `during_print_exhaust_fan_speed` resolve as intended.

## Commit & Pull Request Guidelines
Git history is not yet tracked, so adopt Conventional Commit prefixes (`feat:`, `fix:`, `docs:`) to keep future logs searchable. Keep commits scoped to a single profile family or script change. Pull requests should summarise the scenario, state the Bambu Studio version and snapshot base, link the comparison directory, and attach the validation diff or command output. Update `Anleitung.txt` whenever process changes affect deployment paths or machine support flags.
