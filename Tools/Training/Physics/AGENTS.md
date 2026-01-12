# Repository Guidelines

## Project Structure & Module Organization
- `Tools/Training/Physics/index.html` is a single-file, offline physics trainer (HTML/CSS/JS in one file).
- The in-page calculator has three variants (0 = aus, 1 = freie Eingabezeile mit Live-Vorschau, 2 = Schritt-fuer-Schritt mit Ergebnis-einfuegen pro Zeile); keep those inputs in sync with task data and component lists.
- There is no `src/` or `assets/` folder for this module yet; place new local assets next to `index.html` and use relative paths.
- The circuit SVG draws a closed loop with a simple battery symbol; keep layout changes consistent across series, parallel, and combo circuits.

## Build, Test, and Development Commands
- Open `Tools/Training/Physics/index.html` directly (double click) for offline use.
- Optional local server for relative asset checks: `python -m http.server` from `Tools/Training/Physics`.
- No bundler or build step is used.

## Coding Style & Naming Conventions
- Use 2 spaces for HTML/CSS/JS indentation.
- Keep CSS variables in `:root`, use `kebab-case` for class names, and `camelCase` for JS identifiers.
- Use `CONST_CASE` for fixed lists (e.g., resistor values) and avoid external libraries or CDNs.
- Keep files ASCII-only where possible to preserve offline portability.

## Testing Guidelines
- Manual checks only: refresh multiple times to verify random task generation, circuit drawing, and answer checking.
- Confirm no new task is generated except on first load or when clicking "Neue Aufgabe".
- Verify mobile layout and that circuit labels do not overlap.
- Calculator checks: variant 1 live preview + "Ergebnis einfuegen"; variant 2 step-by-step with `=` line end and per-line "Ergebnis einfuegen" into the term input.

## Commit & Pull Request Guidelines
- Commit history favors short messages (e.g., `upd`, `change`); add a brief hint when possible.
- PRs should include a purpose summary, manual test notes, and a screenshot for UI changes.

## Offline-First Notes
- The page must work by double click with no network access, so keep everything local.
