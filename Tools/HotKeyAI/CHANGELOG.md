# Changelog

All notable changes to PasteSuiteAI are documented in this file.
Format: `[YYYY-MM-DD HH:MM UTC] — Category — Summary`

---

## [2026-02-08 — App Rename + Hotkeys→Actions Refactor]

### App Rename: HotKeyAI → PasteSuiteAI
- **[2026-02-08]** Renamed product from "Paste & Speech AI" / "HotKeyAI" to **PasteSuiteAI** across all layers
- `app_constants.py`: APP_NAME, SERVICE_NAME, APP_DIR_NAME → "PasteSuiteAI"; APP_IDENTIFIER → "com.pastesuite.ai"; ENV_PREFIX → "PASTE_SUITE_AI_"
- `sync_constants.py` stamped new name into `tauri.conf.json` (productName, title, identifier)
- `ui_text.py`: APP_NAME constant propagates to UiTextCatalog defaults

### Concept Rename: Hotkeys → Actions
- **[2026-02-08]** Renamed "Hotkeys" to "Actions" across entire codebase (~287 occurrences, ~27 files)
- **Domain layer**: `HotkeyId` → `ActionId`, `HotkeyDefinition` → `ActionDefinition`, `HotkeyMode` → `ActionMode`, `HotkeyKind` → `ActionKind`, `HotkeyCatalog` → `ActionCatalog`, `HotkeyChanged` → `ActionChanged`
- **Application layer**: `PipelineContext.hotkey` → `.action`, `HotkeySync` → `ActionSync`
- **Infrastructure**: `hotkeys.py` → `actions.py` (`HotkeyAgent` → `ActionAgent`), `hotkey_catalog.py` → `action_catalog.py` (`HotkeyCatalogService` → `ActionCatalogService`)
- **Config**: `HotkeysConfig` → `ActionsConfig`, settings key `hotkeys` → `actions`
- **API endpoints**: `/hotkeys` → `/actions` (all CRUD + execute)
- **Frontend**: All types, state, API methods, component references renamed accordingly
- **JSON files**: `hotkeys.json` → `actions.json` (both backend and frontend/src-tauri)
- **Data migrations**: Added backward-compat migrations in `settings.py`, `action_catalog.py`, `history.py` for existing data files with old key names
- **UI text**: "Hotkeys" → "Actions" in UiTextCatalog
- **Product rule**: Updated from `"Hotkeys" (never "Actions")` to `"Actions" (never "Hotkeys")`

### Documentation
- **[2026-02-08]** Rewrote `CLAUDE.md` — all references updated to PasteSuiteAI + Actions terminology
- **[2026-02-08]** Updated `VIOLATIONS.md` — renamed references
- **[2026-02-08]** Regenerated OpenAPI schema + TypeScript types — `ActionDefinition` in generated-types.ts

---

## [2026-02-08 — SSoT Violation Fixes]

### Phase 1: App Constants SSoT
- **[2026-02-08 14:00 UTC]** Expanded `app_constants.py` with 6 new constants: `BACKEND_PORT`, `FRONTEND_DEV_PORT`, `ALLOWED_HOSTS`, `SERVICE_NAME`, `APP_DIR_NAME`, `ENV_PREFIX`
- **[2026-02-08 14:00 UTC]** Fixed `main.py` — imports `APP_NAME`, `APP_VERSION`, `BACKEND_PORT`, `FRONTEND_DEV_PORT`, `ALLOWED_HOSTS` from app_constants; CORS origins computed from port constants
- **[2026-02-08 14:00 UTC]** Fixed `run_backend.py` — imports `BACKEND_PORT`
- **[2026-02-08 14:00 UTC]** Fixed `secrets.py` — imports `SERVICE_NAME` from app_constants
- **[2026-02-08 14:00 UTC]** Fixed `settings.py` — imports `ENV_PREFIX`, `APP_DIR_NAME` from app_constants
- **[2026-02-08 14:00 UTC]** Fixed `ui_text.py` — uses `APP_NAME` from app_constants in defaults dict
- **[2026-02-08 14:00 UTC]** Fixed `base.py` — mock provider uses `APP_NAME` from app_constants

### Phase 2: UI Text SSoT
- **[2026-02-08 15:00 UTC]** Added 10+ new `UiTextKey` entries: `LABEL_APPEARANCE`, `LABEL_WINDOW_OPACITY`, `LABEL_WINDOW_DECORATIONS`, `LABEL_OK`, `LABEL_CANCEL`, `LABEL_DEL`, `LABEL_ADD_EDIT_CONNECTION`, `PLACEHOLDER_CONNECTION_ID`, `PLACEHOLDER_MODEL_ID`, `PLACEHOLDER_API_KEY`
- **[2026-02-08 15:00 UTC]** `Panel.tsx` — replaced 12 hardcoded strings with `t()` calls
- **[2026-02-08 15:00 UTC]** `Settings.tsx` — replaced 27+ hardcoded strings with `t()` calls
- **[2026-02-08 15:00 UTC]** `ConfirmDialog.tsx` — fixed German default `"Abbrechen"` to `"Cancel"`

### Phase 3: Build-Time Sync Script
- **[2026-02-08 16:00 UTC]** Created `sync_constants.py` — reads `app_constants.py`, stamps values into `package.json`, `tauri.conf.json`, `Cargo.toml`, `vite.config.ts`, `client.ts`. Supports `--check` for CI.

### Phase 4: Provider Registry
- **[2026-02-08 17:00 UTC]** Created `provider_registry.py` — `ProviderRegistration` dataclass + `ProviderRegistry` class
- **[2026-02-08 17:00 UTC]** Added `register_*()` functions to all provider adapters: `base.py` (OpenAI, OpenAI-compatible, Mock), `anthropic.py`, `google.py`, `mistral.py`, `tesseract.py`
- **[2026-02-08 17:00 UTC]** Removed `ProviderFactory` from `pipeline.py` — now uses `registry.create_provider(provider_id)`
- **[2026-02-08 17:00 UTC]** Added `GET /providers` endpoint to `main.py`
- **[2026-02-08 17:00 UTC]** `client.ts` — added `ProviderInfo` type + `getProviders()` method
- **[2026-02-08 17:00 UTC]** `context.tsx` — added `providers` to state, fetched in `refreshData()`
- **[2026-02-08 17:00 UTC]** `Settings.tsx` — replaced hardcoded provider `<option>` list with dynamic `state.providers`

### Documentation
- **[2026-02-08 18:00 UTC]** Updated `VIOLATIONS.md` — moved all fixed P0/P1/P3 entries to Resolved section
- **[2026-02-08 18:00 UTC]** Rewrote `CLAUDE.md` — comprehensive operational guide with SSoT rules, file map, implemented patterns, coding rules, deferred items

---

## [2026-02-08 — Architecture Debt Resolution]

### Phase 1: Value Objects for IDs
- **[2026-02-08 20:00 UTC]** Created `backend/src/domain/types.py` — `ConnectionId`, `HotkeyId`, `ProviderId` via `NewType`
- **[2026-02-08 20:00 UTC]** Updated all domain models, provider registry, secrets, history, hotkey catalog, and all provider adapters to use typed IDs

### Phase 2: Result Type
- **[2026-02-08 20:30 UTC]** Created `backend/src/domain/result.py` — `Ok[T]`, `Err`, `Result = Union[Ok[T], Err]`
- **[2026-02-08 20:30 UTC]** Created `backend/src/domain/errors.py` — `ErrorCategory` enum + `PipelineError` dataclass
- **[2026-02-08 20:30 UTC]** Refactored `pipeline.py` — split into `validate()` and `execute()` returning `Result[T]`; 6 error paths converted from `yield "Error:..."` to `Err(PipelineError(...))`

### Phase 3: Domain Events + EventBus
- **[2026-02-08 21:00 UTC]** Created `backend/src/domain/events.py` — `DomainEvent`, `ExecutionCompleted`, `HotkeyChanged`, `ConnectionChanged`, `SettingsChanged`, `EventBus`
- **[2026-02-08 21:00 UTC]** Created `backend/src/application/handlers.py` — `HistoryRecorder`, `HotkeySync`, `SettingsPersister` event handlers
- **[2026-02-08 21:00 UTC]** Pipeline now publishes `ExecutionCompleted` instead of direct `history.add()`; endpoints publish domain events for side effects

### Phase 4: Composition Root
- **[2026-02-08 21:30 UTC]** Created `backend/src/composition_root.py` — `AppServices` dataclass + `create_services()` wiring function
- **[2026-02-08 21:30 UTC]** Refactored `main.py` — removed ad-hoc service creation; all endpoints use `services.xxx`

### Phase 5: OpenAPI Response Models + Generated TypeScript Types
- **[2026-02-08 22:00 UTC]** Added response models to `domain/models.py`: `ProviderInfoResponse`, `HealthResponse`, `ExecuteResponse`, `StatusResponse`, `SessionTokenResponse`, `HistoryEntryResponse`
- **[2026-02-08 22:00 UTC]** Added `response_model` to all 18 endpoints in `main.py`
- **[2026-02-08 22:00 UTC]** Created `backend/export_openapi.py` — exports OpenAPI schema to JSON
- **[2026-02-08 22:00 UTC]** Added `openapi-typescript` + `npm run generate:types` build step

### Phase 6: Typed Client
- **[2026-02-08 22:30 UTC]** `client.ts` — replaced manual type definitions with imports from `generated-types.ts`; all methods have proper return types
- **[2026-02-08 22:30 UTC]** `context.tsx` — `history: any[]` → `history: HistoryEntry[]`
- **[2026-02-08 22:30 UTC]** Fixed type errors in `Panel.tsx` and `Settings.tsx` from stricter generated types

### Documentation
- **[2026-02-08 23:00 UTC]** Updated `VIOLATIONS.md` — moved all P1/P2 items to Resolved
- **[2026-02-08 23:00 UTC]** Updated `CLAUDE.md` — added new files/patterns, moved deferred items to implemented
- **[2026-02-08 23:00 UTC]** Updated `CHANGELOG.md` — added entries for all 6 phases
