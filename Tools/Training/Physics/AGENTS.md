# Repository Guidelines

## Project Structure & Module Organization
- `Tools/Training/Physics/index.html` is a self-contained training page (HTML, CSS, JS in one file) intended to run offline in the browser.
- There is no separate `src/` or `assets/` directory for this module yet; if new images or data are added, keep them adjacent to `index.html` and reference with relative paths.
- The repository root (`/mnt/d/Github/mcaonline.github.io/`) hosts other tools under `Tools/`, so keep this module isolated and avoid cross-folder dependencies.

## Build, Test, and Development Commands
- Open `Tools/Training/Physics/index.html` directly (double click) to run offline.
- Optional local server for relative asset testing:
  - `python -m http.server` (run from `/mnt/d/Github/mcaonline.github.io/Tools/Training/Physics`), then open `http://localhost:8000/`.
- No bundler, package manager, or build step is used for this module.

## Coding Style & Naming Conventions
- Use 2 spaces for HTML/CSS/JS indentation to keep the single-file layout readable.
- Keep CSS variables in `:root`, use `kebab-case` for class names, and use `camelCase` for JS functions/variables.
- Prefer uppercase `CONST_CASE` for fixed lists (e.g., resistor values) and keep all logic in plain browser JS without external libraries.
- Keep files ASCII-only where possible and avoid external fonts or CDN assets so the page stays offline-first.

## Testing Guidelines
- Manual testing only: refresh multiple times to verify random task generation, circuit drawing, and answer checking.
- Verify both desktop and mobile layouts, especially the circuit SVG scaling and input buttons.
- If you change formula logic, test each mode (U, I, R) and check a few hand calculations.

## Commit & Pull Request Guidelines
- Recent commit history uses short messages (e.g., `upd`, `change`). Keep that style but add a short hint when possible, such as `upd physics trainer UI`.
- Pull requests should include a short purpose summary, a note on manual tests performed, and a screenshot of any UI change.

## Offline-First Notes
- The page must run by double click with no network access, so keep everything local and avoid API calls.
- If you add new files, reference them with relative paths and verify they load without a server.
