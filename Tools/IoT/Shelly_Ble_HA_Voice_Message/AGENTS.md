# Repository Guidelines

## Project Structure & Module Organization
The repository currently centres on `Shelly_HA_Automation_v1.0.txt`, which holds the Home Assistant YAML automation powering Shelly BLE voice notifications. Treat this file as the authoritative source; place new or alternative automations beside it using the pattern `Shelly_HA_Automation_v<major>.<minor>.yaml` so versioned variants stay readable. Add supporting documentation or assets under a matching directory (e.g. `docs/` for diagrams, `audio/` for prompts) and reference them from the automation comments.

## Build, Test, and Development Commands
Use Home Assistant’s config validator before proposing changes. Common options:
- `docker compose exec homeassistant python -m homeassistant --script check_config` — validates YAML in a container install.
- `ha core check` — runs the same validation on Home Assistant OS or Supervised.
- `ha core restart` (after validation) — reloads the automation once deployed.
Keep diffs minimal so reviewers can map commands to edits.

## Coding Style & Naming Conventions
Write automation files in YAML with 2-space indentation, lower_snake_case keys, and descriptive ids (e.g. `pantry_alarm`). Favor anchors or reusable variables for repeated timings. Name media players and satellites exactly as they appear in Home Assistant to avoid runtime mismatches.

## Testing Guidelines
Mirror the durations and entity ids in a staging Home Assistant instance, then run `Settings → Automations → Trace` to confirm the correct branch fires. Provide trace exports or screenshots when a change alters control flow. If adding new triggers, include at least one example sensor in the `variables` block and document expected announcements.

## Commit & Pull Request Guidelines
Compose imperative, scoped commit messages (e.g. “Refine pantry escalation timing”), avoiding one-letter summaries currently in history. PRs should summarise the behavioural change, list verification steps (`check_config`, trace results), link any relevant issue, and attach screenshots of new voice prompts if applicable.

## Configuration & Deployment Tips
Keep sensitive tokens in `secrets.yaml` and reference them via `!secret`. Before merging, double-check time windows (`wk_start`, `we_end`) against local time zone settings. Note any new `assist_satellite` or `media_player` entities in the PR so operators can provision them.
