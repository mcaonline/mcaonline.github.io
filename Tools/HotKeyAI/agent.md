# agent.md — Architecture + SSoT Coding Rules

## 0) Non-negotiables (product)
- UI term: **“Hotkeys”**. Internal code may use `action` but UI strings MUST say “Hotkeys”.
- Defaults on first run:
  - Only `paste_plain_text` hotkey enabled.
  - All other hotkeys/features disabled until explicitly enabled.
  - App works without API keys.
  - AI hotkeys may be created but are **Unavailable** until a compatible provider is connected.
  - `static_text_paste` and `local_transform` work without API keys.
- History:
  - OFF by default.
  - If enabled: default `max_entries = 10` (user can change).
  - History is cleared on app restart.
- Fast path:
  - If text is selected and a hotkey is triggered, execute immediately with no UI.
  - Replace selection in place.
  - Write history only if history enabled.
- Trust/legal:
  - Show “AI can make mistakes…” notice on all input surfaces.
  - Require explicit provider consent checkbox before saving credentials.
  - Keep bilingual legal references in UI text.
- Provider/model:
  - Ship curated offline model catalog.
  - Optional user-triggered “Refresh known models”.
  - Refresh MUST be non-blocking; app stable without refresh.

## 1) SSoT Ownership Map (ONLY these are sources of truth)
- `Domain/Hotkeys/*` → Hotkey definition model (built-in + custom unified).
- `Domain/Settings/*` → Settings schema + defaults + migrations.
- `Domain/Providers/*` → ProviderCatalog + ModelCatalog + Capability graph.
- `UI/UiTextCatalog/*` → All UI strings + legal text. No inline UI strings elsewhere.

Rules:
- No other layer may define “its own” version of these concepts.
- UI renders from domain state only; it never re-derives rules.

## 2) Layering Rules (dependency direction)
- UI → Application → Domain
- Application → Ports (interfaces)
- Adapters (OS/Providers/Storage) implement Ports
- Domain MUST NOT import UI, Adapters, or OS APIs.

## 3) State Model (immutable + event-driven)
- Single in-memory `AppState` object is the runtime truth.
- State changes happen only via `Event -> Reducer(state,event) -> new_state`.
- Side effects are triggered by `Command` objects derived from events/state changes.

Hard rule:
- No direct mutation of state objects. No “setters” outside reducer.

## 4) Execution Pipeline Contract
All hotkey runs follow this pipeline:
1. Capture context (selected text OR clipboard; selected text wins).
2. Resolve hotkey → required capability set.
3. Validate readiness (enabled, consent, credentials, provider availability).
4. Execute transform (local or provider).
5. Apply result (replace selection OR paste to target).
6. Optional history write (only if enabled).

Hard rule:
- Pipeline is the only place allowed to call Ports like clipboard, text injection, network.

## 5) Provider/Capability Model
- Providers expose capabilities: `STT`, `LLM`, `OCR`, `TTS`, etc.
- Each hotkey declares required capability + constraints (streaming? local-only?).
- Selection logic chooses a provider by capability match, user preference, and readiness.

Hard rules:
- No provider-specific branches in UI.
- No direct “if OpenAI then …” inside pipeline. Use capability interfaces.

## 6) Security Rules
- Secrets:
  - Never stored in plaintext.
  - Only stored via OS keychain/credential vault port.
  - Never logged.
- Consent:
  - Credentials may be saved only if consent checkbox true.
  - If no consent: allow temporary session use only (no persistence).
- Least privilege:
  - Default disabled for anything that sends data externally.

## 7) Settings + Migration
- Settings are schema-versioned.
- Changes require:
  - Update schema + defaults.
  - Add migration step for old versions.
- Settings writes are atomic.

Hard rule:
- UI cannot store settings ad-hoc; all settings go through Settings SSoT.

## 8) Error Taxonomy (must use these classes)
- `UserFixable` (missing consent/credentials/invalid selection)
- `Transient` (timeout/rate limit/network)
- `System` (OS permission denied/clipboard inaccessible)
- `Bug` (invariant violated)

UX rule:
- UserFixable: inline guidance + “Fix” action
- Transient: retry button + backoff
- System: blocking dialog + instructions
- Bug: crash-safe report + recovery path

## 9) Observability
- Every hotkey run has `correlation_id`.
- Logs are structured; no secrets; include: hotkey_id, provider_id (if any), error_class.

## 10) Implementation Rules for the AI tool
When coding:
- Create/modify code ONLY in the correct layer per ownership map.
- Never duplicate models between UI and Domain.
- If adding a feature, also add:
  - Invariant checks (domain)
  - At least 1 unit test for domain rule
  - At least 1 integration test for pipeline with fake ports
- Prefer small PR-sized changes.

## 11) Acceptance Checklist (must pass)
- App runs with no API keys; `paste_plain_text` works.
- Creating AI hotkey without credentials results in status: Unavailable (clear reason).
- History off by default; cleared on restart; default max=10 when enabled.
- Selected-text hotkey replaces in place with no UI.
- Refresh models is user-triggered + non-blocking.
- No plaintext secrets; no secrets in logs.
- UI uses “Hotkeys” everywhere.
