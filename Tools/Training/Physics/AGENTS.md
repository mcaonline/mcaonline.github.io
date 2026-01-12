# Repository Guidelines

## Project Structure & Module Organization
- `Tools/Training/Physics/index.html` is a single-file, offline physics trainer (HTML/CSS/JS in one file).
- The in-page calculator has three variants (0 = aus, 1 = freie Eingabezeile mit Live-Vorschau, 2 = Schritt-fuer-Schritt mit Ergebnis-einfuegen pro Zeile); keep those inputs in sync with task data and component lists.
- There is no `src/` or `assets/` folder for this module yet; place new local assets next to `index.html` and use relative paths.
- Rank progress is stored in `localStorage` under `physicsTrainerCorrectCount`; manual rank selection sets the counter to the selected threshold.
- The circuit SVG draws a closed loop with a simple battery symbol; keep layout changes consistent across series, parallel, and combo circuits.

## Build, Test, and Development Commands
- Open `Tools/Training/Physics/index.html` directly (double click) for offline use.
- Optional local server for relative asset checks: `python -m http.server` from `Tools/Training/Physics`.
- No bundler or build step is used.

## Full Spec Recap (From Chat)
- Single offline `index.html` (no server, no external assets) that autogenerates one task on load; a new task appears only when clicking "Neue Aufgabe".
- Default calculator toggle is 0 (hidden) on load.
- Topic: Ohmsches Gesetz `U = R * I` with rearrangements. User selects target variable (U/I/R) or leaves it random; selection affects the next generated task.
- Circuit generation is random: series, parallel (1-5 branches), or combo (series before/after with 0-2 elements plus a parallel block with 2-3 branches). Components are resistors or lamps; lamp is fixed `60 Ohm (Betriebstemperatur)`.
- Component pick uses a small lamp chance (about 25%) otherwise a resistor from the fixed list.
- Combo rule: if both series-before and series-after are empty, insert one series element so the combo circuit still has a series part.
- Resistor values must be typical and easy to compute (e.g., 10/15/20/30/50/60/100/120/150/200/300). No arbitrary random values.
- Given values are picked from fixed arrays (U and I) with a reasonable-result filter so numbers stay in a school-friendly range.
- UI shows: task statement, given values (including lamp note when present), circuit legend (R1/L1 list), answer input with unit, feedback, and a full solution path (Rges + U/I/R calc) after checking. A tips row reminds series/parallel rules.
- Circuit SVG must be a closed loop with a battery symbol; parallel rails should only span between top and bottom branches (no dangling lines). Labels sit under components and must not overlap; adjust vertical spacing for up to 5 parallel branches and avoid collisions in combo circuits with series elements, especially when series parts exist.
- Answer check allows a small tolerance (~2%) and supports comma or dot decimals; Enter in the answer field triggers "Pruefen". Correct answers increase a "richtig" counter only once per task.
- Rank system: thresholds 5/10/20/30/40/50/75/100 with names like `0-Newbie`, `1-Ohm-Rookie`, `2-Unruh`, ... `8-Ultra-Physics-Calculation-Man`. Store count in `localStorage` (`physicsTrainerCorrectCount`). Manual rank selection sets the counter to that threshold. Rank change triggers a small star animation.
- Rank UI includes current rank name, correct-count badge, progress bar, next-rank hint, and a dropdown + "Uebernehmen" button to set the last rank.
- Rechenweg toggle has 0/1/2: 0 hides the calculator, 1 is free input with live preview and "Ausrechnen" to log a line; each logged line has "Ergebnis einfuegen" (insert at cursor) plus per-line "Loeschen". Variant 1 input accepts `1/50` and `1-50` as 1/50, plus words like `plus`, `minus`, `mal`, `geteilt`, `durch`, and `x` or `:` as operators. Enter in the input runs "Ausrechnen".
- Variant 2 is step-by-step with term types (number, 1/number, known, 1/known, last, 1/last), operator selection, live preview, and three buttons: "Wert hinzufuegen", "Rechnungszeile beenden", "Rueckgaengig" (removes last term). Variant 2 lines also support "Ergebnis einfuegen" and per-line delete. "Wert hinzufuegen" requires a non-`=` operator; "Rechnungszeile beenden" finalizes the line with `=`.
- Variant 2 "Bekannter Wert" list includes given U/I, `Rges`, and every component (R1, L1, etc.). "Ergebnis einfuegen" inserts into the active input at the cursor.
- Resolved issues during development: accidental task regeneration on check, label overlap in parallel branches, dangling rails in parallel circuits, cramped spacing for combo series elements, and rank selection button overflow.

## Coding Style & Naming Conventions
- Use 2 spaces for HTML/CSS/JS indentation.
- Keep CSS variables in `:root`, use `kebab-case` for class names, and `camelCase` for JS identifiers.
- Use `CONST_CASE` for fixed lists (e.g., resistor values) and avoid external libraries or CDNs.
- Keep files ASCII-only where possible to preserve offline portability.

## Testing Guidelines
- Manual checks only: refresh multiple times to verify random task generation, circuit drawing, and answer checking.
- Confirm no new task is generated except on first load or when clicking "Neue Aufgabe".
- Verify mobile layout and that circuit labels do not overlap.
- Calculator checks: variant 1 live preview + "Ergebnis einfuegen"; variant 2 live preview with the three buttons ("Wert hinzufuegen", "Rechnungszeile beenden", "Rueckgaengig") and per-line "Ergebnis einfuegen".
- Rank checks: answer correctly to advance at 5/10/20/30/40/50/75/100, confirm the badge updates and the star animation triggers.

## Commit & Pull Request Guidelines
- Commit history favors short messages (e.g., `upd`, `change`); add a brief hint when possible.
- PRs should include a purpose summary, manual test notes, and a screenshot for UI changes.

## Offline-First Notes
- The page must work by double click with no network access, so keep everything local.
