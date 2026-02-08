# SSoT Violations & Design Debt Tracker

Status: Updated 2026-02-08
Audited by: Claude Code
Total violations: 40+ (most resolved)

## How to use this file

Each violation has a priority (P0–P3), category, and fix description.
When fixed, move entry to `## Resolved` section at the bottom with date.

---

## Remaining

- **P2**: `Settings` type in `client.ts` is still manual — backend settings endpoints return `model_dump()` without a Pydantic `response_model`, so OpenAPI schema shows `unknown`. Type was expanded to include all fields from `SettingsSchema`.

---

## Resolved

### 2026-02-08 — P1: Generated TypeScript Types from OpenAPI (fixed)

- Added `response_model` to all 18 endpoints in `main.py`
- Added response models to `domain/models.py`: `ProviderInfoResponse`, `HealthResponse`, `ExecuteResponse`, `StatusResponse`, `SessionTokenResponse`, `HistoryEntryResponse`
- Created `backend/export_openapi.py` — exports OpenAPI schema to `frontend/src/api/openapi.json`
- Installed `openapi-typescript`, added `npm run generate:types` script
- `client.ts` now imports types from `generated-types.ts` instead of manual definitions
- `ConnectionDefinition` and `HotkeyDefinition` types now have all fields (was missing 18+ fields)

### 2026-02-08 — P2: Composition Root / DI (implemented)

- Created `backend/src/composition_root.py` with `AppServices` dataclass and `create_services()` function
- All services wired in dependency order: Settings → SecretStore → Clipboard → HistoryRepo → HotkeyCatalog → ProviderRegistry → EventBus → Pipeline → HotkeyAgent → Event handlers
- `main.py` refactored to use `services.xxx` instead of module-level globals

### 2026-02-08 — P2: Result Type (implemented)

- Created `backend/src/domain/result.py` with `Ok[T]`, `Err`, `Result = Union[Ok[T], Err]`
- Created `backend/src/domain/errors.py` with `ErrorCategory` enum + `PipelineError` dataclass
- Pipeline split into `validate() → Result[PipelineContext]` and `execute() → Result[Iterator[str]]`
- 6 inline `yield "Error:..."` paths replaced with structured `Err(PipelineError(...))`
- Execute endpoint returns HTTP 422 on pipeline errors

### 2026-02-08 — P2: Typed Domain Events + EventBus (implemented)

- Created `backend/src/domain/events.py` with `DomainEvent` base, `ExecutionCompleted`, `HotkeyChanged`, `ConnectionChanged`, `SettingsChanged`
- Created `backend/src/application/handlers.py` with `HistoryRecorder`, `HotkeySync`, `SettingsPersister`
- Pipeline publishes `ExecutionCompleted` event instead of directly calling `history.add()`
- Hotkey CRUD endpoints publish `HotkeyChanged`; settings/connection endpoints publish `SettingsChanged`

### 2026-02-08 — P2: Value Objects for IDs (implemented)

- Created `backend/src/domain/types.py` with `ConnectionId`, `HotkeyId`, `ProviderId` via `NewType`
- Updated all domain models, registry, secrets, history, hotkey catalog, providers
- Pydantic v2 serializes `NewType` as base `str` — zero API contract change

### 2026-02-08 — P2: Generated API Client (implemented)

- `client.ts` types now derived from `generated-types.ts` (OpenAPI schema)
- All `apiClient` methods have proper return types (no `any`)
- `context.tsx` uses `HistoryEntry` type instead of `any[]`

### 2026-02-08 — P0: App Name Duplication (all 7 locations fixed)

`app_constants.py` is the sole definition. Python files import `APP_NAME`. `sync_constants.py` stamps it into `tauri.conf.json` and `package.json`. Frontend reads from `t("app.name")` via UiTextCatalog.

- `backend/src/main.py` → imports `APP_NAME` from `app_constants`
- `backend/src/domain/ui_text.py` → uses `APP_NAME` from `app_constants` in defaults dict
- `frontend/src/components/Panel.tsx` → `{t("app.name")}` instead of hardcoded string
- `frontend/package.json` → stamped by `sync_constants.py`
- `frontend/src-tauri/tauri.conf.json` → stamped by `sync_constants.py` (productName + title)

### 2026-02-08 — P0: Version Duplication (all 5 locations fixed)

One version bump in `app_constants.py` propagates everywhere via imports + sync script.

- `backend/src/main.py` → imports `APP_VERSION` from `app_constants`
- `frontend/package.json` → stamped by `sync_constants.py`
- `frontend/src-tauri/tauri.conf.json` → stamped by `sync_constants.py`
- `frontend/src-tauri/Cargo.toml` → stamped by `sync_constants.py`

### 2026-02-08 — P0: App Identifier Duplication (fixed)

- `frontend/src-tauri/tauri.conf.json` → stamped by `sync_constants.py`

### 2026-02-08 — P0: Hardcoded UI Text in Frontend (40+ strings fixed)

All user-visible strings in `Panel.tsx`, `Settings.tsx`, and `ConfirmDialog.tsx` replaced with `t("key")` calls that fetch from UiTextCatalog via `GET /ui-text`.

- `Panel.tsx` — 12 replacements (app name, status, labels, placeholders, tooltips, buttons)
- `Settings.tsx` — 27+ replacements (header, tabs, section headings, form labels, placeholders, buttons, empty states)
- `ConfirmDialog.tsx` — fixed `"Abbrechen"` → `"Cancel"` default label
- New UiTextKey entries added to `backend/src/domain/ui_text.py`: `LABEL_APPEARANCE`, `LABEL_WINDOW_OPACITY`, `LABEL_WINDOW_DECORATIONS`, `LABEL_OK`, `LABEL_CANCEL`, `LABEL_DEL`, `LABEL_ADD_EDIT_CONNECTION`, `PLACEHOLDER_CONNECTION_ID`, `PLACEHOLDER_MODEL_ID`, `PLACEHOLDER_API_KEY`

### 2026-02-08 — P0: Port Number Duplication (all 9 locations fixed)

`BACKEND_PORT` and `FRONTEND_DEV_PORT` defined in `app_constants.py`. Python files import them. Non-Python files stamped by `sync_constants.py`.

- `backend/run_backend.py` → imports `BACKEND_PORT`
- `backend/src/main.py` → CORS origins computed from port constants, uvicorn uses `BACKEND_PORT`
- `frontend/src/api/client.ts` → stamped by `sync_constants.py`
- `frontend/vite.config.ts` → stamped by `sync_constants.py`
- `frontend/src-tauri/tauri.conf.json` → devUrl stamped by `sync_constants.py`

### 2026-02-08 — P1: Hardcoded Provider Names / String Matching (fixed)

Replaced `ProviderFactory` substring matching with `ProviderRegistry` pattern.

- Created `backend/src/application/provider_registry.py` with `ProviderRegistration` dataclass + `ProviderRegistry` class
- Each provider adapter now has a `register_*()` function: `base.py` (OpenAI, OpenAI-compatible, Mock), `anthropic.py`, `google.py`, `mistral.py`, `tesseract.py`
- `backend/src/main.py` — creates registry, calls all register functions, exposes `GET /providers`
- `backend/src/application/pipeline.py` — removed `ProviderFactory` entirely; resolves providers via `registry.create_provider(provider_id)`
- `frontend/src/components/Settings.tsx` — hardcoded `<option>` list replaced with dynamic list from `state.providers` (fetched via `GET /providers`)
- `frontend/src/api/client.ts` — added `getProviders()` method + `ProviderInfo` type
- `frontend/src/store/context.tsx` — added `providers` to state, fetched in `refreshData`

### 2026-02-08 — P1: Service Name / App Dir Duplication (fixed)

- `backend/src/infrastructure/secrets.py` → imports `SERVICE_NAME` from `app_constants`
- `backend/src/config/settings.py` → imports `APP_DIR_NAME` from `app_constants`

### 2026-02-08 — P1: Localhost/CORS Origins Duplication (fixed)

- `ALLOWED_HOSTS` tuple defined in `app_constants.py`
- Both usages in `backend/src/main.py` (verify_session_token + get_session_token) now import from `app_constants`
- CORS origins computed from `BACKEND_PORT` and `FRONTEND_DEV_PORT` constants

### 2026-02-08 — P2: Hotkey Trigger Display Hardcoded (fixed)

- `Settings.tsx` now reads from `state.settings?.hotkeys?.main_trigger?.chord` instead of hardcoded `"Ctrl + V, V"`

### 2026-02-08 — P2: Build-Time Sync Script (created)

- `sync_constants.py` created at project root
- Reads `app_constants.py` and stamps values into: `package.json`, `tauri.conf.json`, `Cargo.toml`, `vite.config.ts`, `client.ts`
- Supports `--check` mode for CI gating (exits nonzero if any file is stale)

### 2026-02-08 — P2: Provider Self-Registration (implemented)

- See "P1: Hardcoded Provider Names" above — registry pattern now in place
- Adding a new provider = one adapter file + one `register_*()` call. Zero changes to pipeline or UI.

### 2026-02-08 — P3: Environment Prefix (fixed)

- `backend/src/config/settings.py` → imports `ENV_PREFIX` from `app_constants`

### 2026-02-08 — P3: Mock Provider Message (fixed)

- `backend/src/infrastructure/providers/base.py` → imports `APP_NAME`, uses f-string in mock response
