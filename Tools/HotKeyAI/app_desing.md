# HotKeyAI - App Design (Key Decisions)

## Product Goal
HotKeyAI is a lightweight hotkey utility that enhances paste workflows. It supports plain paste, OCR paste, audio transcription paste, and AI transformations triggered from configurable actions.
- Product focus is voice-first productivity: dictation quality and low-friction speech-to-text flows are prioritized over generic feature breadth.

## Terminology Rules (UI vs Backend)
- UI wording must use `Actions` for user-configurable entries.
- Avoid `Hotkey` wording for user-facing configurable entries unless referring to keyboard bindings.
- Backend/API may still use `action` as internal technical terminology.

## Trust, Disclaimer, and Consent (Required)
- Global trust notice text (default):
  - `AI can make mistakes. Please review important outputs before you use or share them.`
- Show this notice on every input surface:
  - main prompt input panel
  - custom action create/edit form
  - provider setup forms where prompts or processing settings are entered
- For no-UI execution flows (direct global hotkey on selected text), user must accept this notice once in settings before direct execution can be enabled.
- Provider legal/privacy consent is mandatory before saving provider credentials.
- Save must be blocked until user checks provider-specific confirmation checkbox for providers below.
- Provider-specific consent copy (bilingual where required):
  - Azure OpenAI:
    - `By adding an Azure key, you confirm that you accept Microsoft usage/data processing terms and are comfortable with Microsoft licensing, contract terms, and data protection (Vertragsbedingungen und Microsoft Datenschutzbestimmungen).`
  - OpenAI:
    - `By adding an OpenAI key, you confirm that you accept OpenAI terms of use and privacy policy (OpenAI Nutzungsbedingungen und Datenschutzrichtlinie).`
  - Mistral:
    - `By adding a Mistral key, you confirm that you accept Mistral terms of use and privacy policy (Mistral Nutzungsbedingungen und Mistral Datenschutzrichtlinie).`
  - Google:
    - `By adding a Google key, you confirm that you accept Google terms of use and privacy policy (Google Nutzungsbedingungen und Google Datenschutzrichtlinie).`
- Consent tracking requirements:
  - persist provider, consent version, and acceptance timestamp
  - if consent text version changes, force re-acceptance before next provider call

## Core User Flow
1. User presses the main HotKeyAI trigger: `Ctrl+V,V` (Ctrl held; press `V`, release `V`, press `V` again while Ctrl is still held).
2. App opens/executes the configured paste action.
3. App captures source input (text/image/audio) based on the action.
4. If the action is AI-powered, app routes the request to the configured model.
5. App pastes output into the previously focused field.
6. App stores a history entry only when history is explicitly enabled by user settings.

## Default Activation Profile (Security-First)
- First run defaults:
  - only `Paste as Plain Text` is enabled
  - all AI-dependent and optional actions are disabled until user enables them
  - history is disabled by default
- History opt-in behavior:
  - when user enables history, default max entries is 10 (user configurable)
  - history is session-memory only (not persisted to disk)
  - history is cleared on app restart or machine reboot

## Primary Trigger Behavior
- Main trigger: `Ctrl+V,V` only.
- Detection rule:
  - `Ctrl` key-down starts an active chord window.
  - First `V` key-down + key-up is required.
  - Second `V` key-down must happen while `Ctrl` is still held.
  - Timeout for second `V`: configurable (default 500 ms).
- On failure (timeout, Ctrl released early, wrong key), pass through normal keyboard behavior and reset state.

## Main Functions After `Ctrl+V,V`
1. Paste as Plain Text
- Inserts clipboard text without formatting or transformation.
- No model/API call.
- Always available, even when no provider connection/API key is configured.

2. Paste Image to Text (OCR)
- Detects image content from clipboard (including screenshots).
- Runs OCR and pastes extracted editable text.
- Optionally post-process OCR result through AI model if user enables it.

3. Paste Audio to Text (Microphone)
- Starts microphone capture.
- Uses configurable dictation mode:
  - live preview mode (partial text updates while speaking)
  - final quality mode (single full transcription after recording ends)
- Pastes final transcription text when transcription completes.

4. Paste Audio File to Text
- Supports drag-and-drop audio files into app or copied audio files from clipboard/file reference.
- Transcribes file audio directly to text and pastes result.

5. Paste Actions (Custom Actions)
- User can define additional actions and a custom prompt per action.
- Source can be text/image/audio based on action definition.
- Action sends source + prompt to selected model, then pastes transformed output.
- If a user assigns a single normal typing key (like `A`) as a global hotkey, show warning: key becomes reserved and no longer types normally while app is active.
- Custom actions may be created before any API key exists; AI-dependent actions remain non-functional until a compatible connection is configured.

## Model Routing (Modular by Design)
Use fully modular model assignment.

- Provider registry supports the final cloud/local provider set.
- Runtime model selection is capability-first through one connection registry.
- Connection record is the single source of truth:
  - provider type
  - capability/purpose (`stt`, `llm`, optional later: `tts`, `embedding`, `ocr`)
  - model id
  - endpoint/deployment metadata
  - secret reference
  - optional model-source flag (`curated` or `custom`)
- Multiple connections can be added per provider (for example one OpenAI LLM + one OpenAI STT).
- Defaults are capability-scoped (not one global model):
  - default STT connection
  - default LLM connection
- Each function/action can override binding by connection id:
  - OCR post-processing connection (optional)
  - Microphone dictation STT connection
  - Audio file transcription STT connection
  - Custom action transform LLM connection
- If an override is not set, use the capability default.
- Validation at save time: block invalid/unavailable connection references.
- If a referenced connection is removed/unavailable, fall back to capability default and show warning.

## Connections Registry (Single Source of Truth)
- Maintain one persisted table/list named `Connections`.
- Every provider setup row is one connection entry.
- Actions never store raw provider/model strings; they store `connection_id` references.
- Voice-first action chaining supports two-stage binding:
  - stage 1: STT connection (transcribe)
  - stage 2: optional LLM connection (post-process/transform)

No-key mode behavior:
- App must run without any cloud provider connection configured.
- Actions that require external AI capability (`llm`/`stt`) can be saved but are marked unavailable until a valid connection exists.
- Local/non-AI actions remain fully available (for example plain text paste and `static_text_paste`).
- AI processing features must not be globally enabled unless at least one valid required capability connection is configured.
- `local_transform` actions require no API key and remain available in no-key mode.

## Supported Provider Set (Final)
Cloud
- OpenAI
- Azure OpenAI
- Anthropic
- Google
- Mistral
- Groq

Local
- Foundry Local
- Ollama
- Tesseract OCR

## Provider and Model Catalog SSoT (Required)
- Keep one canonical manifest (for example `ProviderCatalog`) as single source of truth for:
  - provider ids, display names, and provider class (cloud/local)
  - capability support matrix (`stt`, `llm`, optional later `ocr`, `embedding`, `tts`)
  - curated model catalog entries by provider+capability
- `Supported Provider Set` and `Initial Approved Model Catalog` are views derived from this same manifest; they must not diverge.
- Model strategy is locked:
  - ship a curated offline catalog in-app by default
  - provide optional user-triggered `Refresh known models`
  - refresh must be non-blocking and preserve offline behavior if refresh fails

## Model Picker UX (Required)
When user adds a connection:
- Step 1: select provider.
- Step 2: select capability/purpose:
  - `STT (speech -> text)`
  - `LLM (text -> text)`
  - optional later: `TTS`, `Embeddings`, `OCR`
- Step 3: show model input and selectable model list filtered by provider + selected capability.
- Typing behavior: search/filter over curated list for that provider+capability pair.
- Manual model entry is allowed for advanced users, but must still pass capability validation.
- If typed model does not match selected provider+capability support, block save and show explicit validation message.

## Model Setup Form (Required)
When adding a connection, the form must include:
- Provider selection.
- Capability/purpose selection.
- Model name input (typed) + selectable filtered list under the input.
- API credential input (masked).
- Endpoint/deployment input (only when provider requires it).
- Provider legal/privacy consent notice + required confirmation checkbox when provider is Azure OpenAI, OpenAI, Mistral, or Google.
- Prompt field behavior:
  - LLM connection: system prompt input (multi-line text).
  - STT connection: optional transcription hint/prompt field.

Validation and behavior:
- Same provider type can be configured multiple times as separate connections.
- Connection is the selectable runtime unit in UI.
- Capability is explicit per connection and cannot be ambiguous.
- Model options are capability-scoped:
  - STT-capable model list for STT connections.
  - text/chat-capable model list for LLM connections.
- API credential is required for providers that require authentication.
- For local providers that do not require authentication, API credential can be empty/hidden.
- If provider consent checkbox is required and unchecked, block save and show a clear validation message.
- Save-time hard guardrail:
  - if a model is not valid for the selected provider+capability, block save.
- Validation message for invalid STT picks:
  - `This model cannot be used for speech-to-text. Choose a transcription-capable model.`
- Example guardrail:
  - if user selects OpenAI + `STT` and types `gpt-5.2`, block save and show that it is text-only for this purpose.
- Voice-first warning chip on LLM-only connection setup:
  - `Text-only connection. Add an STT connection for microphone input.`
- System prompt is editable for LLM connections.
- If LLM system prompt is empty, apply the default system prompt below.

Onboarding smart defaults (voice-first):
- First-run wizard should propose creating two connections:
  - recommended STT default:
    - `gpt-4o-mini-transcribe` (faster)
    - or `gpt-4o-transcribe` (highest quality)
  - recommended LLM default:
    - user-selected from enabled provider/model list

Model dropdown strategy (required):
- For each provider+capability pair, show curated known-good model list first.
- Allow manual model entry for advanced usage.
- Persist model source marker:
  - `curated` when selected from built-in list
  - `custom` when manually entered
- Keep curated list usable offline (no network dependency required at runtime settings screen).
- `Refresh known models` is optional and user-triggered; app behavior must remain stable without refresh.

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

## Initial Approved Model Catalog (Now)
Note:
- Catalog is capability-scoped (`LLM` vs `STT`), not one mixed list.
- Availability may vary by region/account/deployment; run setup-time probe call before enabling a connection.
- Dictation standard target is WebUI-like quality via dedicated transcription models.
- Realtime voice conversation is out of scope by product decision.

LLM curated list (text -> text)
- OpenAI Cloud:
  - gpt-5.2
  - gpt-5.2-mini
  - gpt-5.3
  - gpt-5.3-mini
  - o5-mini
- Azure OpenAI:
  - gpt-5.2
  - gpt-5.2-mini
  - gpt-5.3
  - gpt-5.3-mini
  - o5-mini
- Anthropic:
  - claude-4.1
  - claude-4.1-oxford
  - claude-4.1-mini
- Google:
  - gemini-3-pro
  - gemini-3-flash
  - gemini-2.5-pro
  - gemini-2.5-flash
  - gemini-1.5-pro
  - gemini-1.5-flash
- Mistral:
  - mistral-large-2
  - mistral-large
  - mistral-medium
  - mistral-small
  - mixtral-8x7b
  - mixtral-8x22b
- Groq:
  - grok-4
  - grok-4-heavy
- OpenAI OSS / Local:
  - gpt-oss-120b
  - gpt-oss-20b
- Ollama (local):
  - llama4
  - phi3
  - mixtral8x7b
  - gemma3
- Foundry Local:
  - llama-4-scout
  - llama-4-maverick
  - llama-3.1-8b
  - phi-3-medium
  - phi-3-mini

STT curated list (speech -> text)
- OpenAI Cloud:
  - gpt-4o-transcribe
  - gpt-4o-mini-transcribe
  - gpt-4o-transcribe-diarize (if available in account/region)
- Azure OpenAI:
  - gpt-4o-transcribe
  - gpt-4o-mini-transcribe
  - deployment route required
- Google:
  - gemini-2.5-pro (audio input prompting path)
  - gemini-2.5-flash (audio input prompting path)
  - Google Cloud Speech-to-Text backend option (model family must be configured per project)
- Mistral:
  - voxtral-mini-latest
  - additional Voxtral variants when available in account
- Groq:
  - STT endpoint path exists but is excluded from curated voice-first defaults due quality target.
  - advanced custom STT model entry can be enabled manually if team chooses to support it later.
- Anthropic:
  - STT disabled
  - show message: `Claude has no native STT endpoint here. Add a separate STT provider.`
- Local:
  - no STT engine in scope for current version (Whisper intentionally not supported)

OCR list
- Tesseract OCR:
  - tesseract-5.0
  - tesseract-5.2

Embeddings list (optional later capability)
- OpenAI Cloud:
  - text-embedding-3-large
  - text-embedding-3-small

Capability validation guardrails (must enforce)
- If capability is `STT`, only show and allow STT-capable models for that provider.
- If capability is `LLM`, only show and allow LLM-capable models for that provider.
- If user types custom model id that fails provider+capability validation, block save.
- Error text for invalid STT assignment:
  - `This model cannot be used for speech-to-text. Choose a transcription-capable model.`

## Runtime Interaction Model (Required)
Main panel layout and behavior:
- Show current selected connections near prompt area:
  - active LLM connection
  - active STT connection (if available)
  - quick switch controls for each
- Show a compact clipboard preview on the right side of the prompt input area (small preview card).
- Show a prompt input field for user instructions.
- Show a `Dictate` button in/next to prompt input field.
- The action list is shown under the prompt area.
- Clipboard preview must support:
  - text snippet preview
  - image thumbnail preview
  - audio/file preview metadata (file name, duration when available)
- Source priority rule (Windows-first behavior):
  - on trigger, first try to capture selected/marked text from the active control
  - if selected text exists, selected text becomes active source and preview content
  - preview shows a clearly clickable source toggle (for example label/button `Clipboard`) to switch source from selected text to clipboard
  - switching source updates preview immediately
- Dictate button visibility rule:
  - show `Dictate` button only if at least one STT connection is configured and healthy.

Action list behavior (user-facing label: `Actions`):
- List contains built-in transforms and user-defined transforms in one unified modular list.
- Every visible list item is generated from one backend action registry (implemented by the internal action registry as single source of truth).
- Default ordering can start with built-in actions first, but final ordering is fully user-configurable.
- Ordering source of truth:
  - one persisted action registry table contains both built-in and custom actions
  - each action has an explicit sequence position
  - when user reorders in settings, this sequence is updated and runtime panel order changes accordingly
- Each list item must show:
  - action name
  - in-panel quick key hint (`1..9` when assigned)
  - direct/global shortcut hint (if configured) as reminder
- User can trigger action by:
  - clicking the list item
  - pressing in-panel quick key (`1..9` while panel is focused)
  - using configured direct/global shortcut outside panel
- Each action entry must have an `enabled` toggle; disabled entries stay visible but cannot execute.
- Actions missing required AI connection must show `Unavailable` state with reason `API key/provider connection missing`.
- Numbering beyond 9:
  - only first 9 actions in current sequence get numeric quick-key execution in panel
  - actions from index 10 onward remain clickable and direct-hotkey executable
  - if needed later, add paging/search for large action lists instead of ambiguous 2-digit numeric shortcuts
- Quick-key assignment rule:
  - `1..9` are assigned dynamically from current sequence order, not hardcoded per action
  - when sequence changes, visible numeric hints and quick-key mapping update accordingly

Prompt behavior by trigger source:
- Main trigger flow (`Ctrl+V,V`): panel opens, user types instruction prompt, selected action executes with:
  - system prompt from model config
  - user prompt from typed input field
- Direct/global shortcut flow for an action with saved instruction:
  - execute immediately without requiring panel typing
  - system prompt from model config
  - user prompt from action's saved prompt
  - if text is currently selected/marked, do not open UI; process immediately and replace selected text in place
  - when history is enabled, write a history row even when the panel is not shown
- Direct/global shortcut flow for an action without saved instruction:
  - open panel and require typed prompt before execution.
- Dictate prompt entry flow:
  - when `Dictate` button is pressed, start microphone capture and transcribe speech to text using configured STT connection
  - transcription result is inserted into prompt input field (as editable text)
  - if no STT connection exists, `Dictate` button is hidden and action execution is unavailable

Prompt resolution rules:
- Effective system prompt = action/model system prompt if set, otherwise default system prompt.
- Effective user prompt = direct action saved prompt (when present and direct shortcut used), otherwise current typed prompt.
- If effective user prompt is required but empty, block execution and show validation message.
- After successful execution, clipboard preview must refresh immediately to the new clipboard content.
- Selected-text replace rule:
  - if active source is selected/marked text and execution succeeds, replace selected text in-place directly in target control
  - user should only need trigger action + action execution to get selected text replaced

## Custom Action Execution Modes (Required)
Each custom action must declare one execution mode:
- `ai_transform`
  - Uses model provider call with system prompt + user prompt + clipboard source.
- `local_transform`
  - Uses local processing engine only (no external AI call).
  - Requires no provider key and remains available in no-key mode.
  - Supported local transform types:
    - regex replace rules
    - sed-style replacement expressions (compatibility mode)
  - Validate expression syntax at save time.
- `static_text_paste`
  - Ignores clipboard source and pastes predefined text template content.
  - Requires no provider/model/API key and must work in no-key mode.
- `prompt_prefill_only`
  - Supports two explicit panel buttons:
    - `Prefill`: inserts the action prompt into the main prompt input field for review/edit.
    - `Execute Now`: executes immediately using the same effective prompt path as direct action execution.
  - `Prefill` does not execute automatically.

Mode-specific requirements:
- Every custom action still shows direct/global shortcut hint and execution mode badge in panel.
- For direct/global shortcut execution:
  - `ai_transform`, `local_transform`, `static_text_paste` may execute immediately.
  - `prompt_prefill_only` executes immediately when direct shortcut is used; in panel it exposes `Prefill` and `Execute Now`.
- Built-in predefined actions may be non-AI (for example plain text cleanup) and must be clearly marked as local/non-AI.
- Capability gating in no-key mode:
  - `ai_transform` actions are definable but unavailable until required connection/capability exists.
  - unavailable AI actions must show a clear reason and a quick link/button to add provider credentials.

## Action Management Screen (One-Page Required)
- Settings must provide one unified `Actions` page (no split wizard needed for core tasks).
- This page includes built-in and custom actions together in one reorderable list.
- Required operations on the same page:
  - enable/disable each action
  - reorder sequence (drag/drop and move up/down fallback)
  - edit existing custom action
  - add new custom action
- Custom action creation/edit form fields:
  - name (required)
  - description (required)
  - prompt (required for AI/prompt modes)
  - optional direct/global hotkey assignment
- Direct-global selected-text fast path:
  - when selected text exists and a direct hotkey is pressed, process immediately without opening the panel
  - replace selected text in-place on success
  - record processing result in history

## Action-to-Connection Binding (Voice-First)
- All actions reference `connection_id` entries from `Connections`.
- Voice-first actions can chain two connections:
  - required STT connection for microphone/file transcription
  - optional LLM connection for post-transcription transform
- Example binding:
  - action `Dictate -> Correct Grammar` uses `stt_connection_id` first, then `llm_connection_id`.
- On success of STT-only or STT+LLM chain:
  - update clipboard with final text
  - refresh runtime preview immediately

## Voice Dictation and Audio-to-Text (Required)
Two separate audio behaviors must be supported:
- Prompt dictation:
  - user uses `Dictate` button to fill prompt input text inside panel.
- Direct dictation-to-target:
  - dedicated configurable hotkey starts microphone capture without requiring UI to open
  - speech is transcribed and inserted directly at the current cursor/focus target in active application
  - this flow corresponds to direct audio-to-text output

Audio processing mode (configurable):
- `dictate_live_preview_mode`
  - app uses streaming text transcription updates while user is speaking
  - UI shows partial text updates (draft quality)
  - after stop, app may run one final full-pass transcription and replace draft text
- `dictate_final_quality_mode` (default)
  - capture until stop/end-of-speech
  - transcribe full recording after capture completes
  - optional post-processing prompt is applied to transcript before insertion (for example cleanup, rewrite, summary)
  - insertion happens only after transcription/post-processing completes

Scope boundary (explicit):
- `Use Voice` style realtime speech conversation is intentionally out of scope.
- No speech-to-speech flow is allowed.
- No AI voice response playback is allowed.
- This app supports dictation/transcription-to-text only.
- Realtime voice path is disabled by product decision (quality does not meet target and voice reply behavior is not desired).

OpenAI Dictate mapping note:
- Treat ChatGPT "Dictate" style behavior as dictation-first speech-to-text (text output only).
- For OpenAI API integration, use Audio Transcriptions API path for dictation.
- Do not route dictation through realtime voice APIs in this app.
- Product docs do not guarantee one fixed internal model id for ChatGPT Dictate; keep dictation engine configurable in provider settings.
- Default dictation engine should be `gpt-4o-transcribe`.
- `gpt-4o-transcribe` supports both buffered final transcription and streaming text updates.
- Whisper is out of scope and must not be used for dictation in this app.

Audio prompt options:
- Direct dictation hotkey config can include optional post-processing prompt template.
- If post-processing prompt is empty, final insertion uses raw transcript.
- If post-processing prompt is set, transcript is passed through text-processing pipeline before insertion.

Direct dictation rules:
- Must work regardless of whether text is selected.
- UI panel may remain hidden during direct dictation flow.
- If text is selected and target app supports replacement, replace selection; otherwise insert at caret.
- Requires at least one valid STT connection.
- If no STT connection exists, hotkey invocation returns user-visible unavailable notification.
- Capability gating:
  - direct dictation requires `stt` capability.

## API Call Factory Blueprint (Critical)
Goal:
- Implement one internal call factory that builds and executes provider calls consistently across all supported backends.
- Keep provider-specific logic in adapters; keep action logic provider-agnostic.

Factory input contract:
- Task type: `chat_transform`, `embedding`, `audio_transcription`, `ocr`.
- `connection_id` (primary execution connection).
- Capability (`stt`, `llm`, `embedding`, `ocr`).
- Provider group (resolved from connection).
- Model label (resolved from connection).
- Endpoint base URL (resolved from connection, if required).
- Deployment alias (resolved from connection, when provider routes by deployment).
- Secret reference (resolved from connection, never raw key in config).
- System instruction text.
- User instruction text.
- Optional source text.
- Optional source image bytes (PNG).
- Optional source audio file path.
- Optional chained `next_connection_id` (for STT -> LLM post-processing pipeline).
- Execution options: timeout, retry policy.

Factory output contract:
- Normalized result object with:
  - status (`ok` or `error`)
  - output kind (`text`, `embedding_vector`, `transcript`, `ocr_text`)
  - output payload
  - usage metadata (when provider returns token usage)
  - provider error class and retriable flag (if failed)

Execution pipeline (must follow exactly):
1. Validate provider-model-task compatibility (capability matrix).
2. Resolve secret from SecretStore (if provider requires secret).
3. Build provider-specific URL, headers, and JSON payload.
4. Execute HTTP/local call with timeout and retry policy.
5. Parse provider response into normalized output.
6. Map provider errors into unified app error categories.
7. Return normalized output to action dispatcher.

API version management:
- Pin explicit provider API versions where versioned endpoints are used.
- Store API version overrides in non-secret provider config only when required.
- Re-run provider conformance tests whenever a provider API version is changed.

### Capability Matrix Rules
- `chat_transform` allowed only for text-generation/vision-capable models.
- `embedding` allowed only for embedding-capable models.
- `audio_transcription` allowed only for transcription-capable backends.
- `ocr` allowed only for OCR-capable local backends.
- Model labels that are embedding-only must be rejected for chat transforms.
- STT hard rules by provider:
  - OpenAI/Azure: allow only transcription-model entries for STT purpose.
  - Google: allow only configured audio-capable path (Gemini-audio prompting or Cloud STT backend).
  - Mistral: allow only Voxtral STT entries.
  - Groq: STT is off by default for voice-first quality target; allow only if explicitly enabled as advanced custom path.
  - Anthropic: reject STT purpose and show `No STT support in this provider path.`

### Prompt Assembly Rules
For text-only transforms:
- System instruction: top-level system/developer instruction field if provider supports it.
- User payload text format:
  - user instructions first
  - then source content
  - then explicit output cue

Recommended user payload template:
- `User instructions:\n{instruction}\n\nSource content:\n{source_text}\n\nOutput:`

For image-assisted transforms:
- Send user text + image in provider-native multimodal format.
- Image bytes must be PNG and encoded as base64 when required by provider.

### Provider Call Specs (Implement As Written)
OpenAI Cloud (`chat_transform`, `embedding`, optional moderation)
- Chat URL: `https://api.openai.com/v1/chat/completions`
- Auth header: `Authorization: Bearer <api_key>`
- Required headers: `Content-Type: application/json`
- Chat payload minimum:
  - `model`
  - `messages` array
- Multimodal user message:
  - text part + image part (data URL: `data:image/png;base64,<...>`)
- Parse chat result from first choice message content.
- Embeddings URL: `https://api.openai.com/v1/embeddings`
- Embeddings payload minimum:
  - `model`
  - `input`
- Parse embedding from first vector entry.
- Optional moderation URL: `https://api.openai.com/v1/moderations`
- Moderation payload minimum:
  - `input`
  - optional explicit moderation model
- Audio transcription URL: `https://api.openai.com/v1/audio/transcriptions`
- Audio transcription request format:
  - `multipart/form-data`
  - include audio file field + transcription model field (`gpt-4o-transcribe` by default)
  - optional language/prompt fields when needed
  - optional streaming mode when app wants incremental text updates before final transcript
- Parse transcript text from transcription response body.
- Dictation quality recommendation:
  - use `gpt-4o-transcribe` for primary dictation quality.
  - do not use Whisper in this app.
  - do not use Realtime Voice API in this app.

Azure OpenAI (`chat_transform`, `audio_transcription`)
- Chat URL mode A (deployment route):
  - `{azure_endpoint}/openai/deployments/{deployment_alias}/chat/completions?api-version=2024-10-21`
- Chat URL mode B (v1 route where available):
  - `{azure_endpoint}/openai/v1/chat/completions`
- Auth header: `api-key: <api_key>`
- Required headers: `Content-Type: application/json`
- Payload minimum:
  - mode A: `messages`
  - mode B: `model`, `messages`
- Deployment alias rule:
  - if deployment alias is empty, use selected model label as deployment alias.
- Parse result from first choice message content.
- Implementation rule:
  - choose one Azure mode per provider configuration and validate it with a setup-time test call.
- STT route:
  - use Azure OpenAI audio transcription endpoint path for configured deployment.
  - deployment must point to transcription-capable model (`gpt-4o-transcribe` or `gpt-4o-mini-transcribe`).
  - request format: multipart audio upload + deployment/model selection.
  - parse transcript text from transcription response.

Anthropic (`chat_transform`, multimodal when needed)
- URL: `https://api.anthropic.com/v1/messages`
- Auth headers:
  - `x-api-key: <api_key>`
  - `anthropic-version: 2023-06-01`
- Required headers: `Content-Type: application/json`
- Payload minimum:
  - `model`
  - `max_tokens`
  - `messages`
- System instruction:
  - use top-level system field when provided.
- Multimodal content block format:
  - image block with source (`base64` + media type + data)
  - text block for user instruction/context
- Parse assistant text by concatenating returned text blocks.
- STT support:
  - disabled in this app/provider path.
  - setup validation must reject `stt` capability for Anthropic connections.

Google (`chat_transform`, multimodal when needed, optional `audio_transcription` path)
- URL format:
  - `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
- Auth header: `x-goog-api-key: <api_key>`
- Required headers: `Content-Type: application/json`
- Payload minimum:
  - `contents` with user parts
- System instruction:
  - include in provider-native system instruction field.
- Image input:
  - inline data block with `mime_type` and base64 `data`.
- Parse text by concatenating candidate content text parts from first candidate.
- STT path options:
  - Gemini audio prompting path: audio input + transcription prompt, parse text output.
  - Google Cloud STT backend path: use dedicated speech endpoint configured per project.
  - one path must be selected in connection settings and validated by setup probe.

Mistral (`chat_transform`, optional `audio_transcription`)
- URL: `https://api.mistral.ai/v1/chat/completions`
- Auth header: `Authorization: Bearer <api_key>`
- Required headers: `Content-Type: application/json`
- Payload minimum:
  - `model`
  - `messages`
- Parse result from first choice message content.
- STT path:
  - use Mistral transcription endpoint with Voxtral STT model selection (for example `voxtral-mini-latest`).
  - multipart audio upload; parse transcript text from response.

Groq (`chat_transform`, optional `audio_transcription`)
- URL: `https://api.groq.com/openai/v1/chat/completions`
- Auth header: `Authorization: Bearer <api_key>`
- Required headers: `Content-Type: application/json`
- Payload minimum:
  - `model`
  - `messages`
- Parse result from first choice message content.
- STT path:
  - disabled by default in this app due voice-first quality target.
  - if explicitly enabled, use Groq speech-to-text endpoint with provider-supported transcription models.
  - multipart audio upload; parse transcript text from response.

OpenAI OSS / Local (`chat_transform`)
- No single universal cloud endpoint is assumed.
- Route through a local-runtime adapter (default: Ollama-compatible adapter).
- Maintain model alias mapping in config:
  - UI label -> runtime model identifier.
- Default alias mapping (initial):
  - `gpt-oss-120b` -> `gpt-oss:120b`
  - `gpt-oss-20b` -> `gpt-oss:20b`

Ollama (local) (`chat_transform`)
- Local URL: `http://localhost:11434/api/chat`
- Required headers: `Content-Type: application/json`
- Local auth: none (default local runtime)
- Payload minimum:
  - `model`
  - `messages`
  - `stream: false` (for simple synchronous pipeline)
- Parse output from assistant message content.

Foundry Local (`chat_transform`)
- Use local runtime adapter (SDK/runtime integration), not generic internet endpoint.
- Required checks before call:
  - runtime availability
  - selected local model installed/loaded
- Required payload concept:
  - system instruction
  - user message text
- Parse final assistant text from runtime response object.

Tesseract OCR (`ocr`)
- Use local OCR adapter (offline/local execution).
- Input:
  - image bytes or image file path
  - optional OCR language code.
- Output:
  - normalized extracted text.
- Apply OCR preprocessing pipeline before OCR call (grayscale/contrast/denoise) when enabled.

### Endpoint and Auth Validation Rules
- Providers requiring endpoint must fail fast if endpoint missing.
- Providers requiring API key must fail fast if secret missing.
- Providers not requiring API key must ignore empty secret references safely.
- Save-time validation must verify endpoint format and provider-model compatibility.

### Timeout, Retry, and Failure Mapping
- Default connect timeout: 10 seconds.
- Default request timeout: 120 seconds (longer for transcription when configured).
- Retry policy:
  - retry on 429 and 5xx with exponential backoff + jitter
  - do not retry on auth/validation errors (4xx except 429)
  - max retry attempts: 3
- Unified failure mapping:
  - `connection_required`
  - `auth_error`
  - `endpoint_error`
  - `rate_limited`
  - `provider_unavailable`
  - `invalid_model_for_task`
  - `timeout`
  - `unexpected_provider_error`

### Provider Conformance Tests (Must Pass Before Release)
For each enabled provider adapter, run automated smoke tests:
- Health/config test:
  - endpoint format valid
  - required secret exists
  - selected model passes capability validation for task type
- Minimal call test:
  - execute one minimal text transform call with deterministic short prompt
  - verify non-empty parsed result in normalized response format
- Error behavior test:
  - invalid key returns `auth_error`
  - invalid model returns `invalid_model_for_task` or provider equivalent mapped error
  - forced timeout returns `timeout`
- Retry behavior test:
  - synthetic 429/5xx path triggers retry with capped attempts
  - non-retriable 4xx path does not retry

Release gate:
- A provider cannot be marked "production ready" until all above tests pass in CI and local integration environment.

### Non-Negotiable Implementation Notes
- Keep provider adapters isolated so adding/removing provider does not change action logic.
- Never log raw request payloads containing user clipboard content unless explicit local debug mode is enabled.
- Never store API keys in settings or history.
- Return deterministic, structured error payloads so UI can display clear recovery guidance.

## Final Architecture Decision
Use a **decoupled architecture**:
- **Backend/Core first** in Python (business logic only, no GUI).
- **Frontend later** in Flutter.

This keeps the UI replaceable and avoids lock-in while using Python strengths for AI logic.

## Tech Choices
- **Frontend target:** Flutter (Windows, macOS, Linux, Android later).
- **Backend target:** Python service.
- **Communication:** local API (`HTTP/FastAPI` initially; `gRPC` optional later).
- **Contracts:** explicit request/response schemas (JSON/OpenAPI now, protobuf if gRPC is added).

## Concrete Runtime Topology (MVP)
Use a 3-component local architecture even before Flutter UI ships:
- `HotkeyAgent` (OS-native): captures global hotkeys/chords and forwards normalized trigger messages.
- `CoreService` (Python/FastAPI): executes all business logic, provider routing, transcription/OCR, history, and paste orchestration.
- `UIClient` (Flutter later): settings/history/status UI only; no business logic.

Runtime communication:
- `HotkeyAgent -> CoreService`: local authenticated IPC (localhost + token/nonce).
- `UIClient -> CoreService`: same contract surface as hotkey path.
- `CoreService -> HotkeyAgent`: optional callback channel for "paste now" key injection and focus restore.

Design constraints:
- Hotkey handler must do minimal work; never run OCR/AI/transcription directly in hook context.
- Core must be callable without UI running.
- UI failure must not break background action execution.

## Credential Security Strategy (Cross-OS)
Adopt a secure credential-handling pattern aligned with modern desktop/mobile best practices:
- Keep API keys in OS credential vaults.
- Keep `settings.json` for non-secret config only (provider type, model, endpoint, actions, hotkey bindings, routing).
- Never store API keys in registry, plaintext config, logs, telemetry, or clipboard.

This is the approved/state-of-the-art baseline for desktop/mobile apps:
- OS-managed secret store per user/device
- at-rest encryption handled by platform security subsystem
- app-level least-privilege access through a dedicated secret-store abstraction

### Backend SecretStore Abstraction
Implement a backend interface:
- Save secret by connection reference and service category.
- Read secret by connection reference and service category.
- Delete secret by connection reference and service category.
- List secret references (metadata only, no secret values).

Provider config and secret are separated:
- Config file stores provider metadata and routing only.
- SecretStore stores API keys/tokens keyed by connection id.

### OS-Specific Secret Backends
Windows
- Use Windows Credential Manager APIs.
- Use per-user secure storage only; do not introduce custom plaintext credential files.

macOS
- Use Keychain Services (`kSecClassGenericPassword` entries scoped to app/service).

Linux
- Use Secret Service API (`libsecret`, GNOME Keyring/KWallet backend).
- If desktop secret service is unavailable, block cloud provider enablement until secure store is available (no plaintext fallback).

Android
- Use Android Keystore-backed encrypted storage (Keystore + EncryptedSharedPreferences/EncryptedFile).
- Keep provider metadata separate from secret material.

Any other OS (future)
- Prefer native secure keychain/credential APIs first.
- If no secure OS store exists, require explicit user-provided master passphrase and encrypted local vault (Argon2id + AES-256-GCM/XChaCha20-Poly1305). Disabled by default.

### Registry and Config Policy
- Registry is allowed only for non-secret OS integration flags/policies.
- `settings.json` may include endpoint URL, model name, deployment id, connection id, provider id, and capability purpose.
- `settings.json` must never include API key, bearer token, refresh token, or raw auth headers.

### Secret Lifecycle Rules
- Add connection: save key to SecretStore; write connection metadata to config.
- Edit connection key: overwrite key in SecretStore.
- Remove connection: remove key from SecretStore and delete connection metadata.
- Export/import settings: export without secrets; import requires re-entering keys.
- Migration: if legacy plaintext key is found, migrate once into SecretStore and immediately erase plaintext source.

### Provider Credential Rules (Concrete)
- Credentials are keyed by connection reference plus service category, never by model name.
- Endpoint URL is non-secret config and must stay in settings; API keys/tokens stay in SecretStore only.
- Providers that do not require API keys (for example local-only backends) must store empty secret refs, not fake values.
- Credential read failures must degrade action availability (disable affected connection) and surface actionable error text.

## Backend Scope (Must Have)
- Hotkey command handling interface.
- Chord detector for `Ctrl+V,V` with timeout + reset rules.
- Input capture pipelines:
  - Active selected/marked text capture from focused control (Windows-first behavior)
  - Clipboard plain text
  - Clipboard image/screenshot OCR
  - Microphone capture + transcription (`dictate_live_preview_mode` or `dictate_final_quality_mode`)
  - Audio file transcription
- Voice input pipelines:
  - Prompt dictation pipeline (`Dictate` button -> prompt input field text)
  - Direct dictation pipeline (hotkey -> transcribe -> insert into focused target)
- Prompt routing per custom action.
- Local transform pipeline for custom actions:
  - regex rule execution
  - sed-style replacement compatibility mode
- Static text template paste pipeline for custom actions.
- Prompt-prefill action mode pipeline (`Prefill` and `Execute Now` interaction paths).
- Unified ordered action registry persistence pipeline:
  - one table/list for built-in + custom actions
  - persisted sequence position
  - dynamic `1..9` quick-key mapping from current sequence
- Connection capability registry:
  - per-connection capability (`stt`, `llm`, optional later `tts`, `embedding`, `ocr`)
  - runtime gating for features based on capability availability
- Connection routing layer with:
  - multi-connection registry
  - capability defaults (default STT, default LLM)
  - per-function and per-action overrides via `connection_id`
  - safe fallback when referenced connection is missing
- Provider abstraction:
  - OpenAI
  - Azure OpenAI
  - Anthropic
  - Google
  - Mistral
  - Groq
  - Foundry Local
  - Ollama
  - Tesseract OCR
- Output handling for paste-back.
- In-place selected text replacement path when selected-text source is active.
- History storage with configurable retention.
- Config management (actions, prompts, providers, model routing, defaults) with strict secret/config separation.
- Secret management layer with OS-specific secure credential storage backends.

## Hotkey/Trigger Engine Spec (Concrete)
State machine for main trigger `Ctrl+V,V`:
- `Idle` -> `CtrlHeld` on Ctrl down.
- `CtrlHeld` -> `FirstVPressed` on first V down while Ctrl held.
- `FirstVPressed` -> `FirstVReleased` on first V up while Ctrl held.
- `FirstVReleased` -> `Triggered` on second V down while Ctrl still held and timeout not exceeded.
- Any unexpected key, timeout, or Ctrl release returns to `Idle` with no interception side effects.

Operational rules:
- Configurable timeout (default 500 ms) applies only between first V up and second V down.
- Second V on timeout boundary is treated as failure (deterministic).
- Synthetic key events emitted by app paste-back must be marked and ignored by hotkey detection to prevent recursion.
- Chord engine emits structured trigger outcomes: accepted, rejected, timed out, cancelled.

## Action Execution Contract (Concrete)
Every action follows one pipeline:
1. Resolve action descriptor (type, required input formats, connection routing, prompt template).
2. Snapshot source context (clipboard/focus/window target/audio source).
3. Validate capabilities and provider availability before heavy work.
4. Execute transform with cancellation token and progress channel.
5. Validate output package (text/file/image) is pasteable.
6. Paste back and restore focus.
7. Write history + audit-safe telemetry.

Required execution controls:
- Single active action lock per user session.
- User-visible cancel for long AI/transcription actions.
- Min/Max operation timeouts per action type.
- Distinct error classes: `input_unavailable`, `connection_required`, `provider_unavailable`, `moderated`, `timeout`, `unexpected`.

## Input Capability Resolution Rules
Before showing or executing an action, compute available input capabilities:
- `text`, `html`, `image`, `audio_stream`, `audio_file`, `file_ref`.
- Action availability is computed from declared required capabilities, not UI assumptions.
- If input is incompatible, action is disabled and response includes machine-readable reason.
- For image OCR and audio file transcription, file type probing must be explicit and deterministic.

## Connection Routing Specification (Concrete)
Routing precedence (highest to lowest):
1. Per-action `connection_id` override.
2. Per-function `connection_id` override.
3. Capability default connection (`default_stt_connection_id` or `default_llm_connection_id`).

Default connection behavior:
- STT default and LLM default are independent and explicit.
- If a default connection is deleted, fallback is the most recently validated connection of same capability.
- If no valid connection exists for required capability, dependent actions are unavailable while unrelated actions remain functional.

Provider abstraction requirements:
- Each provider declares capability support matrix by purpose.
- Router refuses assignments to connections that do not satisfy required purpose/capability.
- Provider health probe endpoint must exist for settings validation and startup diagnostics.
- If execution requires a missing/invalid connection, return deterministic unavailable state with remediation (`add API key/provider connection`).

## History and Persistence Rules (Concrete)
- Store history as structured records with: unique id, timestamp, action reference, input type, output type, connection reference(s), provider reference, model reference, duration, and status.
- History is disabled by default and must be explicitly enabled (opt-in).
- When enabled, default retention is 10 entries; configurable by count.
- Runtime/session behavior:
  - history list shows the latest action runs from current app session by default
  - configurable max history count determines both remembered and visible history depth in session UI
- Persistence scope:
  - history is memory-only for current session
  - history is not written to disk by default
  - history is cleared on app restart and machine reboot
- History content storage policy:
  - store input source snapshot, effective prompt text, and output text for each history row when available
  - never store secrets or auth metadata
- History row reuse options:
  - copy input back to clipboard
  - copy output back to clipboard
  - load prompt back into prompt input field
- Temporary files created for paste-as-file/transcode/transcription artifacts must be cleaned by TTL job.

## Settings and Schema Evolution
- Maintain explicit settings schema versioning.
- On load: run migrations sequentially until current schema.
- Migrations must be idempotent and safe on partial failure.
- Unknown fields must be preserved where possible for forward compatibility.
- Connection references and capability compatibility must be validated at save and load.

## UI Text Catalog Contract (SSoT)
- Maintain one versioned `UiTextCatalog` store for all user-visible strings:
  - labels, descriptions, notices, legal consent text, status text, and error messages
- UI components must reference text keys; no duplicated inline hard-coded strings in runtime/settings/history surfaces.
- Catalog evolution rules:
  - adding text requires adding a new key in catalog only
  - key rename/removal requires migration alias mapping until all consumers are updated
  - missing key fallback must be deterministic (fallback language or safe default string)

## Error Handling and UX Contract
- All API errors return a structured response with an error code, user-facing message, retryability indicator, and redacted details.
- User-facing messages must be actionable and mapped from low-level exceptions.
- Moderation blocks return dedicated code and never leak raw provider safety payloads.
- Paste action failures must not corrupt clipboard state.
- Add explicit error code: `connection_required` for AI actions invoked without a valid configured connection.
- Default user message for this case:
  - `This action needs an API provider connection. You can add your API key now; until then this action stays unavailable.`

## Observability and Privacy Rules
- Emit structured logs with correlation id per action.
- Metrics: action latency, success/failure counts, provider error rates, timeout rates, cancellation rates.
- Redaction policy:
  - never log clipboard payloads by default
  - never log API keys/tokens/endpoints with embedded credentials
  - allow debug payload logging only behind explicit local-dev flag

## Testing and Quality Gates
Required test layers:
- Unit: hotkey state machine, routing precedence, provider capability checks, fallback logic.
- Contract: API request/response schema tests for all action endpoints.
- Integration: OCR, transcription, provider adapters, SecretStore implementations.
- Resilience: cancellation, timeout, unavailable provider, missing connection override.

Required release gates:
- No plaintext secret persistence in any tested path.
- Chord detector deterministic under rapid key sequences.
- Paste-back recursion guard verified.
- Migration tests for at least previous two schema versions.

## Frontend Scope (Later)
- Settings UI for:
  - Main trigger config and timing
  - Default activation profile controls (security-first defaults with only plain text paste enabled on first run)
  - One-page `Actions` manager (built-in + custom in one unified list with enable/disable, reorder, edit, add)
  - Custom action editor (name, description, prompt, optional direct hotkey)
  - No-key onboarding UX: allow creating actions without API setup; mark AI actions as `Not ready` with CTA to add provider key/connection
  - Configurable hotkey for direct dictation/audio-to-text output
  - Dictation mode selector (`dictate_live_preview_mode` / `dictate_final_quality_mode`)
  - Action order manager (drag/drop or move up/down) across built-in and custom entries
  - Custom action mode selector (`ai_transform`, `local_transform`, `static_text_paste`, `prompt_prefill_only`)
  - Local transform editor (regex and sed-style expression validation)
  - Static text template editor
  - Connection manager (provider + capability + model + credentials + endpoint/deployment)
  - Provider consent checkbox UI for Azure/OpenAI/Mistral/Google with links to terms and privacy policies
  - Purpose-first picker (`STT` or `LLM`) before model list appears
  - Provider+purpose-aware model picker with typed filter input + curated list + custom model entry
  - STT capability guardrails and save-time validation messages
  - Capability defaults (`default STT connection`, `default LLM connection`)
  - Per-function and per-action connection override selectors
  - Global trust notice placement: `AI can make mistakes...` on all prompt/input surfaces
  - History opt-in controls (off by default), in-memory session-only retention, and max-count configuration
- Runtime panel UI for:
  - Current selected STT and LLM connection indicators + quick switch controls
  - Clipboard preview card + typed prompt input
  - `Dictate` button in prompt field (visible only when at least one STT connection is available)
  - Source toggle control in preview (`Selected` / `Clipboard`) when selected text is available
  - History button on the right side under/near the prompt row
  - Unified modular action list from backend action registry
  - Visible quick-key and direct-hotkey hints per action item
  - Execution mode badge per custom action item
  - For `prompt_prefill_only`: two visible buttons (`Prefill`, `Execute Now`)
  - Click and keyboard execution paths with same backend action id
- History viewer as table/list with columns/fields for input, prompt, output and quick reuse options.
- Status/errors and per-action connection visibility.
- Drag-and-drop target for audio file transcription.

## Design Rules for Future Development
- Keep business logic out of UI.
- Every core feature must be callable via API.
- UI must be swappable without changing backend behavior.
- Add tests at backend contract boundaries first.
- Any new AI feature must explicitly define model fallback behavior.
- Any credential-bearing feature must use SecretStore and pass secret-handling tests.
- All UI state must be derivable from backend API responses; no hidden UI-only business rules.

## Product Design Principles
1. **Action Registry SSoT**
Why: A single canonical action model prevents drift between built-in and custom actions and keeps ordering/enablement deterministic.
How: Store both built-in and custom actions in one `Actions` registry with `id, name, description, prompt, binding, enabled, position, capability, connection_id, ui_metadata`, and render all screens from that ordered source.

2. **UI Text SSoT**
Why: Centralized UI copy avoids duplicated hard-coded strings and keeps labels, legal text, and localization consistent.
How: Keep all display text in a versioned `UiTextCatalog` (key/value) and have settings, runtime panel, and history resolve labels by key instead of inline literals.

3. **Capability-First Provider Registry + Factories**
Why: Capability-based routing scales better than provider-specific branching as STT/LLM/OCR integrations grow.
How: Register each provider once with a declared capability matrix, then build execution clients through factories using `capability + connection_id` as the lookup contract.

4. **Strict Separation of Concerns**
Why: Decoupling UI, domain, execution, storage, and integrations reduces duplication and keeps the voice-first pipeline maintainable.
How: Keep provider calls and action orchestration in CoreService, while UI only issues typed commands and renders typed responses.

5. **Immutable State + Event-Driven Flow**
Why: Predictable state transitions are critical for hotkey-heavy async behavior and reliable undo/history semantics.
How: Use immutable state snapshots and domain events (`ActionTriggered`, `ExecutionCompleted`, `HistoryRecorded`) to drive reducer-style updates.

6. **Interface-Driven DI**
Why: Dependency injection enables clean swapping of providers, OS services, and test doubles without touching domain rules.
How: Bind interfaces (`ISecretStore`, `IClipboardPort`, `IHotkeyHook`, `IProviderClient`) in one composition root per platform.

7. **Strong Typing + Schema Validation + Migrations**
Why: Typed contracts and guarded migrations prevent settings corruption and runtime breakage across app upgrades.
How: Version the settings schema, validate on read/write, and run idempotent migrations that preserve unknown forward-compatible fields.

8. **Traceable Observability + Error Taxonomy**
Why: Fast incident diagnosis requires run-level traceability across UI, execution pipeline, and providers.
How: Emit structured logs/metrics with a correlation id per run and map failures to a fixed taxonomy (`input_unavailable`, `connection_required`, `provider_unavailable`, `timeout`, `moderated`, `unexpected`).

9. **Security and Secret Hygiene by Default**
Why: API keys and transformed user content are sensitive and must never leak through convenience shortcuts.
How: Store secrets only in OS keychain facilities, enforce least-privilege access, and block plaintext key/payload logging in all non-debug paths.

10. **Cross-Platform Ports + Testability as a First-Class Constraint**
Why: Windows/macOS/Linux differences should be isolated so behavior stays deterministic and reusable.
How: Put OS-specific code behind adapters and enforce deterministic unit tests, provider contract tests, and golden tests for prompt/action execution outputs.

## Implementation Priority
1. Define backend API contracts and typed models (actions, capability matrix, routing schema, error schema).
2. Implement hotkey/chord state machine module with deterministic tests (`Ctrl+V,V` + recursion guard).
3. Build SecretStore abstraction + first OS backend (Windows), with strict secret/config split tests.
4. Build provider registry + routing engine (capability declarations, fallback behavior, health probes).
5. Build API call factory + provider adapters using the call blueprint in this document.
6. Implement core action dispatcher with lifecycle controls (lock, cancellation, progress, timeout).
7. Implement plain text and OCR pipelines end-to-end with paste-back and history write.
8. Implement microphone transcription and audio-file transcription pipelines end-to-end.
9. Implement voice dictation flows:
   - `Dictate` button to fill prompt field
   - direct dictation hotkey to insert transcribed text at focused target
   - both dictation modes (`dictate_live_preview_mode` and `dictate_final_quality_mode`)
10. Implement custom actions + action modes (`ai_transform`, `local_transform`, `static_text_paste`, `prompt_prefill_only`) + per-action connection override.
11. Implement unified ordered action registry + settings reorder controls + dynamic `1..9` quick-key reassignment.
12. Implement connection capability matrix and runtime gating (`stt`, `llm`, optional later capabilities).
13. Add local transform engine (regex + sed compatibility) with save-time validation and tests.
14. Add settings schema versioning, migration framework, and config watcher reload behavior.
15. Add structured observability (correlation ids, metrics, redaction policy).
16. Add contract/integration/resilience test suites and release gates.
17. Build Flutter UI against stable backend API.
