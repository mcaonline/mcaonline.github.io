# HotKeyAI Architecture and Design Specification (Refactored)

Version: 1.1.0-refactor2  
Status: Implementation Ready  
Normative language: `MUST`, `MUST NOT`, `REQUIRED`, `OPTIONAL`.

## Product Scope and Defaults

### Product Scope
HotKeyAI is a cross-platform, voice-first, hotkey-driven desktop app for transforming and inserting content at the current cursor target. Supported source/input domains:
- Selected text from active control
- Clipboard text
- Clipboard image/screenshot (OCR)
- Microphone audio (speech-to-text)
- Audio file transcription

Out of scope:
- Realtime speech-to-speech conversation
- Voice playback responses
- Whisper-based dictation pipeline

### Terminology Contract
- User-facing term is `Hotkeys`.
- Backend/internal execution term may be `action`.
- UI must not expose `Actions` as the primary user-facing label.
- Keyboard binding terminology remains `hotkey`, `chord`, `quick key`.
- Legacy compatibility: where migration from old UI copy is required, `Actions` may appear only as a temporary alias (`Hotkeys (formerly Actions)`) for one migration cycle, then removed.

### Non-Negotiable Defaults (Security-First)
On first run:
- Only `Paste as Plain/Unformatted Text` is enabled.
- All other built-in and custom hotkeys/features are disabled until explicitly enabled by the user.
- History is `OFF` by default.
- The app is fully usable without API keys.

No-key mode requirements:
- AI-dependent hotkeys can be created and saved.
- AI-dependent hotkeys remain unavailable until a compatible provider connection exists.
- `static_text_paste` and `local_transform` remain available without API keys.

### History Policy
- History is opt-in only.
- Default max entries when enabled: `10`.
- Max entries is user-configurable.
- History is session-memory only.
- History is cleared on app restart or machine reboot.

### Primary Trigger and Direct Hotkey Fast Path
Main trigger:
- `Ctrl+V,V` chord (Ctrl held, V press-release, V press while Ctrl remains held).
- Second `V` timeout default: `500 ms` (configurable).

Direct selected-text fast path:
- If text is selected and a direct hotkey is triggered, execution must start immediately without opening UI.
- On success, selected text is replaced in place.
- History row is written only when history is enabled.

## SSoT Architecture Contracts

This section defines the only authoritative stores. Any UI/API/feature document deriving overlapping facts must reference these stores and must not redefine them.

### Contract A: `HotkeyCatalog` (Canonical Runtime Unit)
Single source of truth for all executable entries (built-in + custom) in one unified model.

Required fields:
```ts
HotkeyDefinition {
  id: string;                         // stable UUID
  kind: 'builtin' | 'custom';
  mode: 'ai_transform' | 'local_transform' | 'static_text_paste' | 'prompt_prefill_only';
  display_key: string;                // UiTextCatalog key
  description_key: string;            // UiTextCatalog key
  enabled: boolean;
  sequence: number;                   // ordering SSoT
  direct_hotkey?: string;             // global binding
  panel_quick_key?: 1|2|3|4|5|6|7|8|9; // derived at runtime from sequence
  capability_requirements: CapabilityRequirement[];
  input_requirements: InputRequirement[];
  llm_connection_id?: string;
  stt_connection_id?: string;
  prompt_template?: string;
  local_transform_config?: LocalTransformConfig;
  static_text_template?: string;
  created_at: string;
  updated_at: string;
}
```

Rules:
- Built-in and custom entries must live in the same registry.
- UI ordering, enablement, availability, and quick-key hints are derived from this catalog only.
- Only first 9 ordered enabled entries receive quick keys `1..9`.
- Entries at index >= 10 remain clickable and direct-hotkey executable.
- No feature may maintain a second ordering source.
- Mode semantics are contract-bound and must not be redefined elsewhere:
  - `ai_transform`: provider-backed transform using connection routing.
  - `local_transform`: local-only transform; REQUIRED supported types are regex rules and sed-style replacement compatibility mode; expression syntax must be validated at save time.
  - `static_text_paste`: pastes predefined static template text and ignores source payload.
  - `prompt_prefill_only`: panel must expose `Prefill` (fill prompt only, no execution) and `Execute Now` (immediate execution).
- Direct hotkey safety rule: if a single printable typing key (example: `A`) is bound globally, UI must show an explicit warning that normal typing for that key becomes reserved while app hotkeys are active.

### Contract B: `UiTextCatalog` (Canonical User Text)
Single source of truth for all user-visible copy.

Scope includes:
- Labels, descriptions, notices, legal text, validation text, status text, error text.

Rules:
- UI must render text by catalog key.
- Inline hardcoded user-facing copy is prohibited except deterministic fallback text.
- Catalog keys are versioned and migrated; key removals require alias mapping for one migration cycle.

Required global trust notice key/value:
- Key: `trust.ai_mistakes_notice`
- Value: `AI can make mistakes. Please review important outputs before you use or share them.`

Required provider consent text keys (verbatim values managed only in `UiTextCatalog`):
- `consent.azure_openai.required`
- `consent.openai.required`
- `consent.mistral.required`
- `consent.google.required`

Required default values:
- `consent.azure_openai.required`:
  - `By adding an Azure key, you confirm that you accept Microsoft usage/data processing terms and are comfortable with Microsoft licensing, contract terms, and data protection (Vertragsbedingungen und Microsoft Datenschutzbestimmungen).`
- `consent.openai.required`:
  - `By adding an OpenAI key, you confirm that you accept OpenAI terms of use and privacy policy (OpenAI Nutzungsbedingungen und Datenschutzrichtlinie).`
- `consent.mistral.required`:
  - `By adding a Mistral key, you confirm that you accept Mistral terms of use and privacy policy (Mistral Nutzungsbedingungen und Mistral Datenschutzrichtlinie).`
- `consent.google.required`:
  - `By adding a Google key, you confirm that you accept Google terms of use and privacy policy (Google Nutzungsbedingungen und Google Datenschutzrichtlinie).`

### Contract C: `ProviderCatalog` (Canonical Capability + Model Truth)
Single source of truth for provider metadata, capability support, and curated model catalog.

Required structure:
```ts
ProviderCatalog {
  catalog_version: string;
  providers: ProviderDefinition[];
  curated_models: CuratedModelDefinition[];
}
```

Provider fields include:
- `provider_id`, `display_name`, `class` (`cloud|local`), capability matrix (`stt|llm|ocr|embedding|tts`), endpoint/auth strategy, consent requirement flag.

Model fields include:
- `provider_id`, `capability`, `model_id`, `status`, `source='curated'`.

Rules:
- Supported provider list and model picker options are derived views, never manually duplicated.
- Curated model catalog ships offline in-app.
- `Refresh known models` is optional, user-triggered, and non-blocking.
- Refresh failure must not block app startup or runtime execution.
- Manual custom model entry is allowed but must pass provider+capability validation before save.

Initial curated catalog seed must be defined in `ProviderCatalog` (not in separate docs/tables):
- LLM:
  - OpenAI Cloud: `gpt-5.2`, `gpt-5.2-mini`, `gpt-5.3`, `gpt-5.3-mini`, `o5-mini`
  - Azure OpenAI: `gpt-5.2`, `gpt-5.2-mini`, `gpt-5.3`, `gpt-5.3-mini`, `o5-mini`
  - Anthropic: `claude-4.1`, `claude-4.1-oxford`, `claude-4.1-mini`
  - Google: `gemini-3-pro`, `gemini-3-flash`, `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-1.5-pro`, `gemini-1.5-flash`
  - Mistral: `mistral-large-2`, `mistral-large`, `mistral-medium`, `mistral-small`, `mixtral-8x7b`, `mixtral-8x22b`
  - Groq: `grok-4`, `grok-4-heavy`
  - OpenAI OSS/Local: `gpt-oss-120b`, `gpt-oss-20b`
  - Ollama (local): `llama4`, `phi3`, `mixtral8x7b`, `gemma3`
  - Foundry Local: `llama-4-scout`, `llama-4-maverick`, `llama-3.1-8b`, `phi-3-medium`, `phi-3-mini`
- STT:
  - OpenAI Cloud: `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, `gpt-4o-transcribe-diarize` (account/region dependent)
  - Azure OpenAI: `gpt-4o-transcribe`, `gpt-4o-mini-transcribe` (deployment route required)
  - Google: `gemini-2.5-pro`, `gemini-2.5-flash`, optional Google Cloud STT backend path
  - Mistral: `voxtral-mini-latest`, additional Voxtral variants when available
  - Groq: STT adapter path exists but is disabled by default for voice-quality policy
  - Anthropic: STT not supported in this app/provider path
  - Local: no STT engine in scope for current version
- OCR:
  - Tesseract OCR: `tesseract-5.0`, `tesseract-5.2`
- Embeddings (optional capability):
  - OpenAI Cloud: `text-embedding-3-large`, `text-embedding-3-small`

### Contract D: `SettingsSchema` (Canonical Configuration Persistence)
Single source of truth for non-secret persisted state.

Rules:
- Secrets must not exist in settings.
- Settings version is explicit and migration-driven.
- Unknown fields must be preserved where possible.

Required top-level domains:
- `app`
- `hotkeys`
- `connections`
- `routing_defaults`
- `history`
- `privacy`
- `diagnostics`

### Derived Data Rule (Anti-Duplication)
The following are derived-only views and may not become independent persisted truth:
- Runtime hotkey list UI
- Quick-key assignment map
- Provider setup dropdowns
- Capability availability badges
- User-facing error text selection

## Runtime and Execution Model

### Runtime Topology
- `HotkeyAgent` (OS adapter): captures global input and forwards normalized trigger events.
- `CoreService` (domain + pipeline): authoritative orchestration, routing, validation, execution, history.
- `UIClient` (desktop UI): renders state, dispatches commands, owns no business rules.

Concrete MVP stack decisions:
- `CoreService`: Python + FastAPI local service boundary.
- `UIClient`: Flutter desktop client (Windows/macOS/Linux).
- Hotkey and UI communication with core: localhost IPC with per-session token/nonce authentication.
- Transport evolution: JSON/OpenAPI first; optional gRPC/protobuf later behind unchanged domain contracts.
- `CoreService` must be callable with `UIClient` not running.
- `UIClient` failure must not break background hotkey execution paths.

### Architectural Boundaries
- UI layer: presentation only.
- Domain layer: immutable state, reducers, policy rules.
- Execution layer: pipelines, dispatcher, cancellation/timeout.
- Storage layer: settings/history repositories.
- Integration layer: provider adapters, OS ports, keychain ports.

### Ports/Interfaces (Required)
```ts
IHotkeyPort
IClipboardPort
ISelectionPort
IPastePort
ISecretStore
IProviderRegistry
IProviderFactory
IProviderClient
ISettingsRepository
IHistoryRepository
IEventBus
```

OS-specific adapters implement ports for Windows/macOS/Linux. Domain layer must remain OS-agnostic.

### Immutable State + Event Model
State updates must be reducer-driven and event-triggered.

Required domain events:
- `HotkeyTriggered`
- `ExecutionStarted`
- `ExecutionProgressed`
- `ExecutionSucceeded`
- `ExecutionFailed`
- `HistoryRecorded`
- `ConnectionHealthChanged`
- `SettingsMigrated`

Rules:
- Reducers are pure.
- Side effects execute in handlers/services, never in reducers.
- Every execution run has a correlation id.

### Trigger State Machine (`Ctrl+V,V`)
States:
- `Idle -> CtrlHeld -> FirstVPressed -> FirstVReleased -> Triggered`

Failure reset conditions:
- Timeout exceeded
- Ctrl released early
- Wrong key event sequence

Operational rules:
- Timeout applies between first `V` release and second `V` press.
- Timeout boundary is deterministic: boundary-exact late key is failure.
- Synthetic paste-back key events must be tagged and ignored to prevent recursion.

### Execution Pipeline Contract
For every run:
1. Resolve `HotkeyDefinition` from `HotkeyCatalog`.
2. Snapshot source context (selection/clipboard/audio/file/focus target).
3. Resolve effective connections by precedence:
   1. Hotkey-specific override
   2. Function-specific override
   3. Capability default (`default_stt_connection_id`, `default_llm_connection_id`)
4. Validate capability, provider availability, and consent/credentials.
5. Execute mode pipeline (`ai_transform`, `local_transform`, `static_text_paste`, `prompt_prefill_only`).
6. Validate output and paste/replace in target.
7. Emit telemetry + write history if enabled.

Concurrency rules:
- Single active execution lock per user session.
- New trigger while busy returns deterministic `busy` rejection.
- User cancellation must be supported for long-running runs.

### Prompt Resolution Rules
- Effective system prompt: connection-level/system prompt if set; otherwise default system prompt.
- Effective user prompt:
  - direct hotkey with saved prompt -> use saved prompt
  - panel flow -> use typed prompt
- If required user prompt is empty, execution is blocked with validation error.
- Post-success runtime rule: clipboard/source preview must refresh immediately after a successful run.

Default system prompt:
```text
You are an assistant for text processing.

Your task is to strictly follow the user’s instruction to transform the provided text
(e.g. reformat, rewrite, summarize, correct, translate, or adapt tone or style).

Rules:
- Output ONLY the transformed text.
- Do NOT add explanations, comments, or metadata.
- Do NOT repeat the original text unless explicitly instructed.
- Preserve meaning and intent unless the user requests otherwise.
- Keep the original language unless a translation is explicitly requested.
- If formatting is requested, apply it cleanly and consistently.
- If the input is empty or invalid, output nothing.
```

### API Call Factory Contract (Required)
All provider calls must pass through one capability-first call factory; feature code must not build provider HTTP payloads directly.

Factory input contract:
```ts
ProviderCallRequest {
  task_type: 'chat_transform' | 'embedding' | 'audio_transcription' | 'ocr';
  connection_id: string;
  capability: 'llm' | 'stt' | 'embedding' | 'ocr';
  provider_id: string;              // resolved from connection
  model_id: string;                 // resolved from connection
  endpoint_base_url?: string;       // resolved from connection
  deployment_alias?: string;        // resolved from connection
  secret_ref?: string;              // never raw secret
  system_instruction?: string;
  user_instruction?: string;
  source_text?: string;
  source_image_png_base64?: string;
  source_audio_file_path?: string;
  next_connection_id?: string;      // STT -> LLM chain
  timeout_ms?: number;
  retry_policy?: RetryPolicy;
}
```

Factory output contract:
```ts
ProviderCallResult {
  status: 'ok' | 'error';
  output_kind?: 'text' | 'embedding_vector' | 'transcript' | 'ocr_text';
  output_payload?: unknown;
  usage?: { input_tokens?: number; output_tokens?: number; total_tokens?: number };
  error_code?: 'auth_error' | 'endpoint_error' | 'invalid_model_for_task' | 'rate_limited' | 'provider_unavailable' | 'timeout' | 'unexpected';
  retryable?: boolean;
  provider_error_class?: string;
}
```

Factory pipeline:
1. Validate capability matrix for provider+model+task.
2. Resolve secret from `ISecretStore` when required.
3. Build provider-native URL/headers/payload in adapter.
4. Execute call with timeout/retry policy.
5. Parse provider response into normalized result.
6. Map provider-specific failures to canonical app errors.

Versioning rule:
- Provider API versions must be explicit in adapter config where applicable.
- Changing pinned API version requires rerunning provider conformance tests before release.

### Provider Adapter Call Specs (Required)
OpenAI Cloud:
- Chat URL: `https://api.openai.com/v1/chat/completions`
- Embeddings URL: `https://api.openai.com/v1/embeddings`
- Moderations URL (optional): `https://api.openai.com/v1/moderations`
- Audio transcription URL: `https://api.openai.com/v1/audio/transcriptions`
- Auth: `Authorization: Bearer <api_key>`
- Required header: `Content-Type: application/json` (multipart for audio transcription)
- Parse rule: text from first choice message content; embeddings from first vector entry; transcript text from transcription response body.

Azure OpenAI:
- Route A: `{azure_endpoint}/openai/deployments/{deployment_alias}/chat/completions?api-version=2024-10-21`
- Route B (where available): `{azure_endpoint}/openai/v1/chat/completions`
- Auth: `api-key: <api_key>`
- Required header: `Content-Type: application/json`
- Deployment alias rule: if alias is empty, use selected model id as deployment alias.
- STT route must point deployment to a transcription-capable model.

Anthropic:
- URL: `https://api.anthropic.com/v1/messages`
- Auth headers: `x-api-key: <api_key>`, `anthropic-version: 2023-06-01`
- Required header: `Content-Type: application/json`
- STT policy: unsupported; setup validation must reject Anthropic `stt` connections.

Google:
- URL: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
- Auth: `x-goog-api-key: <api_key>`
- Required header: `Content-Type: application/json`
- STT path policy: each connection must choose Gemini-audio prompting path or Cloud STT backend path; selection must pass setup probe.

Mistral:
- URL: `https://api.mistral.ai/v1/chat/completions`
- Auth: `Authorization: Bearer <api_key>`
- Required header: `Content-Type: application/json`
- STT path: transcription endpoint with Voxtral model.

Groq:
- URL: `https://api.groq.com/openai/v1/chat/completions`
- Auth: `Authorization: Bearer <api_key>`
- Required header: `Content-Type: application/json`
- STT path is disabled by default; advanced enablement is explicit.

Ollama:
- URL: `http://localhost:11434/api/chat`
- Required header: `Content-Type: application/json`
- Default local auth: none.

Foundry Local:
- Adapter contract requires runtime availability check and installed model check before execution.

Tesseract OCR:
- Local adapter only (offline execution), optional preprocessing (grayscale/contrast/denoise) before OCR call.

### OpenAI Dictation Mapping (Required)
- Dictation must use OpenAI Audio Transcriptions API path, not Realtime Voice APIs.
- Default dictation model id is `gpt-4o-transcribe`.
- Streaming partial text updates are allowed in `dictate_live_preview_mode`.
- Buffered final transcription is required in `dictate_final_quality_mode`.
- Whisper is out of scope for this product version.

## Security, Privacy, and Consent

### Secret Handling
- API keys/tokens must be stored only in OS secure storage.
- Plaintext secrets in files, registry, logs, telemetry, clipboard, or history are prohibited.

Approved secret backends:
- Windows: Credential Manager
- macOS: Keychain Services
- Linux: Secret Service (`libsecret`)

If secure store is unavailable:
- Cloud provider enablement is blocked.
- No plaintext fallback is allowed.
- Legacy migration rule: if a legacy plaintext key is detected during migration, app must migrate it once into secure store and immediately erase plaintext source.

### Config vs Secret Separation
`SettingsSchema` may store:
- provider id, connection id, model id, endpoint URL, deployment alias, capability.

`SettingsSchema` must not store:
- raw API key, bearer token, refresh token, auth headers.

Provider credential rule:
- Providers that do not require authentication (local-only paths) must persist empty `secret_ref` values, never fake placeholders.

### Consent and Legal Requirements
Provider consent checkbox is required before saving credentials for:
- Azure OpenAI
- OpenAI
- Mistral
- Google

Consent persistence must include:
- `provider_id`
- `consent_version`
- `accepted_at`

If consent text version changes:
- Re-acceptance is mandatory before next provider call.

Required bilingual legal references in UI text catalog:
- Nutzungsbedingungen
- Datenschutzrichtlinie
- Vertragsbedingungen
- Microsoft Datenschutzbestimmungen

### Trust Notice Placement
The notice `AI can make mistakes...` must appear on all input surfaces:
- Main prompt input
- Hotkey create/edit forms
- Provider setup forms with prompt/processing input

For no-UI direct execution flows:
- One-time trust acknowledgement in settings is required before enabling direct AI execution.

### Privacy and Data Minimization
- Default logging excludes user payload content.
- Content logging is allowed only under explicit local debug mode.
- Telemetry is redacted and correlation-id based.

## Provider and Model Registry Design

### Supported Providers (Current)
Cloud:
- OpenAI
- Azure OpenAI
- Anthropic
- Google
- Mistral
- Groq

Local:
- Foundry Local
- Ollama
- Tesseract OCR

### Capability-First Provider Registry
Registry contract:
- Provider declares capabilities and required auth/endpoint mode.
- Factory resolves `IProviderClient` by capability + connection.
- Domain logic never branches directly by provider name.

Example capability policies:
- Anthropic `stt`: not supported, hard reject.
- Groq `stt`: disabled by default, optional advanced path.
- OpenAI/Azure `stt`: transcription models only.
- Mistral `stt`: Voxtral-only entries.

### Connection Model (Execution Unit)
Each connection is one persisted record with:
- `connection_id`
- `provider_id`
- `capability` (`stt|llm|ocr|embedding|tts`)
- `model_id`
- `model_source` (`curated|custom`)
- `endpoint/deployment metadata`
- `secret_ref`
- optional system prompt/transcription hint
- health status

Rules:
- Multiple connections per provider are allowed.
- Defaults are capability-scoped, never global.
- Invalid connection references are blocked at save time.
- Missing/deleted connection fallback: most recent healthy connection of same capability; if none, dependent hotkeys are unavailable.
- Probe-before-enable rule: a new/edited connection remains disabled until setup-time probe succeeds (endpoint/auth/model/capability validation).

Voice chaining rule:
- Voice-first pipelines may bind two connections in order:
  1. `stt_connection_id` for transcription.
  2. optional `llm_connection_id` for post-transcription transform.
- If chain stage 2 is absent, stage 1 transcript is final output.

### Model Picker Contract
Add connection flow:
1. Select provider.
2. Select capability (`STT` or `LLM`; others optional later).
3. Select model from filtered curated list or enter custom model id.
4. Enter credentials/endpoint fields as required.
5. Accept provider consent when required.

Validation:
- Provider+capability+model compatibility must pass before save.
- Invalid STT model message:
  - `This model cannot be used for speech-to-text. Choose a transcription-capable model.`
- Setup probe is required before marking connection healthy/usable.
- Voice-first warning for LLM-only setup:
  - `Text-only connection. Add an STT connection for microphone input.`

Onboarding defaults (voice-first):
- First-run setup should propose creating two connections:
  - recommended STT default: `gpt-4o-mini-transcribe` (faster) or `gpt-4o-transcribe` (highest quality)
  - recommended LLM default: user-selected from available provider/model options

### Curated Catalog and Refresh Rules
- App ships with offline curated catalog.
- `Refresh known models` is user-triggered only.
- Refresh is background-only and cancel-safe.
- Refresh cannot freeze settings or runtime hotkey execution.
- Last known good catalog remains active if refresh fails.

## Hotkeys UX and Behavior Rules

### Unified Hotkeys UX
- Runtime panel lists built-in and custom hotkeys from unified `HotkeyCatalog`.
- Each row shows name, enabled state, mode badge, quick-key hint, and direct hotkey hint.
- Disabled hotkeys remain visible but not executable.
- Unavailable AI hotkeys show reason `API key/provider connection missing` and a setup CTA.
- Runtime panel prompt zone requirements:
  - Active LLM connection indicator + quick switch.
  - Active STT connection indicator + quick switch.
  - Right-side compact source preview card (text snippet/image thumbnail/audio or file metadata).
  - Prompt input with `Dictate` button.
  - History button placed under/near prompt row on the right.

### Execution Paths
Main trigger (`Ctrl+V,V`):
- Opens panel unless direct selected-text fast path applies.

Direct/global hotkey:
- With saved prompt: execute immediately.
- Without saved prompt: open panel and require prompt input.
- If selected text exists: bypass UI and replace in place on success.

History write rule:
- Write row only when history is enabled.

### Source Priority and Toggle
On trigger:
- Attempt selected text capture first.
- If selected text exists, selected text becomes active source.
- UI exposes source toggle (`Selected` / `Clipboard`).
- Switching source updates preview immediately.

### Dictation Rules
Two flows:
- Prompt dictation: `Dictate` fills prompt input field.
- Direct dictation hotkey: transcribes and inserts/replaces text in target app without opening panel.

Mode options:
- `dictate_live_preview_mode`
- `dictate_final_quality_mode` (default)

Capability gating:
- Dictation requires healthy `stt` connection.
- If unavailable, invocation returns deterministic unavailable notification.

Direct insertion behavior:
- Direct dictation must work whether or not text is selected.
- If text is selected and target supports replacement, replace selection.
- Otherwise insert at current caret position.
- Optional post-processing prompt may be configured per direct dictation hotkey:
  - empty post-processing prompt => insert raw transcript
  - non-empty post-processing prompt => transcript passes through text-processing pipeline before insertion

`prompt_prefill_only` behavior:
- Panel must show `Prefill` and `Execute Now`.
- `Prefill` writes prompt text into input field and does not execute.
- `Execute Now` executes immediately using normal prompt resolution rules.

### Settings Screen Requirements
Single-page `Hotkeys` management must support:
- Enable/disable
- Reorder
- Add/edit custom hotkeys
- Custom hotkey editor fields:
  - `name` (required)
  - `description` (required)
  - `prompt_template` (required for `ai_transform` and `prompt_prefill_only`)
  - optional `direct_hotkey`
- Configure mode (`ai_transform`, `local_transform`, `static_text_paste`, `prompt_prefill_only`)
- Assign direct hotkeys
- Assign connection overrides
- Validate and warn on single-key global bindings that reserve normal typing keys.
- Local transform editor with regex and sed-style validation feedback.
- Static text template editor for `static_text_paste`.
- Drag-and-drop target for audio file transcription.

## Error Taxonomy and Recovery UX

### Canonical Error Codes
- `input_unavailable`
- `connection_required`
- `consent_required`
- `auth_error`
- `endpoint_error`
- `invalid_model_for_task`
- `rate_limited`
- `provider_unavailable`
- `timeout`
- `busy`
- `moderated`
- `unexpected`

### Error Response Contract
```ts
AppError {
  code: ErrorCode;
  message_key: string;      // UiTextCatalog key
  retryable: boolean;
  remediation_key?: string; // UiTextCatalog key
  details_redacted?: object;
  correlation_id: string;
}
```

### Recovery Rules
- Retry policy applies only to `429` and `5xx`; max attempts `3` with exponential backoff + jitter.
- Auth/validation errors are non-retriable.
- Timeout defaults:
  - connect timeout: `10s`
  - request timeout: `120s` (transcription may use higher configured bound)
- Failure must not corrupt clipboard state.
- UI messaging must be actionable and deterministic by `message_key`.

Default `connection_required` UX text contract:
- `This action needs an API provider connection. You can add your API key now; until then this action stays unavailable.`

## Settings Schema and Migration Strategy

### Schema Versioning
- `settings.schema_version` is required.
- App must run sequential idempotent migrations on load until current version.
- Partial migration failure triggers rollback to last valid snapshot and safe-mode startup.

### Required Schema Domains (Example)
```json
{
  "schema_version": 1,
  "app": {},
  "hotkeys": {
    "catalog": [],
    "main_trigger": { "chord": "Ctrl+V,V", "second_v_timeout_ms": 500 }
  },
  "connections": [],
  "routing_defaults": {
    "default_stt_connection_id": null,
    "default_llm_connection_id": null
  },
  "history": {
    "enabled": false,
    "max_entries": 10
  },
  "privacy": {
    "trust_notice_ack_for_direct_ai": false
  },
  "diagnostics": {
    "debug_payload_logging": false
  }
}
```

History record contract (session-memory only):
- `history` entries should include: run id, timestamp, hotkey id, input type, output type, connection refs, provider/model refs, duration/status.
- Content snapshots (input/prompt/output text) are optional per privacy mode but when enabled must remain local and never include secrets.
- Row reuse actions: copy input, copy output, load prompt.

Temporary artifact policy:
- Temporary files created for transcription/transcode/paste artifacts must be tracked and deleted by TTL cleanup job.

### Migration Rules
- Preserve unknown forward-compatible fields whenever structurally possible.
- Validate all `connection_id` references at save and load.
- Recompute quick-key assignments after each migration that changes ordering.
- Export/import excludes secrets by design; reconnect requires credential re-entry.
- Legacy plaintext secret migration must be one-way: import to secure store, erase plaintext immediately, never re-export plaintext.

## Observability and Test Strategy

### Observability
Required telemetry dimensions:
- execution latency
- success/failure counts
- provider error rates
- timeout rates
- cancellation rates

Rules:
- Every run has correlation id propagated through UI, core, provider adapter.
- Logs are structured and redacted by default.
- Payload logging is disabled unless explicit local debug flag is enabled.

### Test Strategy and Release Gates
Unit tests:
- Chord state machine determinism
- Routing precedence
- Capability validation
- Reducer/event correctness

Contract tests:
- API request/response schemas
- Error contract mapping
- `UiTextCatalog` key coverage for message keys
- Provider adapter conformance (endpoint/auth/payload/parse contracts, pinned version behavior)

Integration tests:
- Provider adapters
- Secret store implementations
- OCR pipeline
- STT pipeline
- Selected-text replacement path
- Setup probe-before-enable behavior for new/edited connections
- STT -> optional LLM chained pipeline behavior

Resilience tests:
- Timeout, cancellation, retries, provider outage
- Missing credentials/consent
- History off/on behavior and session reset
- Temporary artifact TTL cleanup

Mandatory release gates:
- No plaintext secret persistence in any tested path.
- Direct selected-text fast path behavior verified.
- History writes only when enabled.
- Migration tests pass for at least previous two schema versions.
- Provider conformance suite passes for every enabled provider adapter.

## Implementation Roadmap

1. Define typed contracts for `HotkeyCatalog`, `ProviderCatalog`, `UiTextCatalog`, `SettingsSchema`, and `AppError`.
2. Implement composition root with DI bindings and platform ports.
3. Implement chord detector (`Ctrl+V,V`) with deterministic state machine tests.
4. Implement secure `ISecretStore` adapters (Windows/macOS/Linux).
5. Implement capability-first provider registry and provider factory.
6. Implement connection manager, capability-scoped defaults, and health probing.
7. Implement execution dispatcher and mode pipelines (`ai_transform`, `local_transform`, `static_text_paste`, `prompt_prefill_only`).
8. Implement selected-text capture and in-place replacement fast path.
9. Implement dictation flows (prompt dictation and direct dictation) with STT gating.
10. Implement session-memory history with opt-in default off and default max=10.
11. Implement settings migrations, import/export (no secrets), and rollback-safe load path.
12. Implement observability, redaction, and error taxonomy mapping.
13. Execute test gates and provider conformance suite.
14. Ship UI surfaces wired only through contracts and catalog keys.

## Open Questions (only if needed)
None. All previously conflicting rules are resolved in this refactor.

## Refactor Change Log
- Normalized user-facing terminology to `Hotkeys`; confined `action` to backend/internal contracts.
- Merged duplicate/contradictory rules into single deterministic policies (history writes, fast path behavior, defaults, routing precedence).
- Converted high-level principles into enforceable contracts with explicit schemas, interfaces, and execution rules.
- Consolidated provider/model definitions under `ProviderCatalog` SSoT and removed drift-prone duplicate listing semantics.
- Hardened security/compliance text into operational requirements (consent versioning, keychain-only secrets, legal text keys).
- Added implementation-grade error taxonomy, migration strategy, observability requirements, and release gates.
- Reintroduced missing implementation constraints from source spec (provider call factory contract, adapter call specs, dictation mapping, setup probes, history/TTL details) while keeping SSoT boundaries intact.
