"""
Composition Root — the single place where all services are instantiated and wired.

Call create_services() once at startup. Returns an AppServices container that
main.py uses to wire FastAPI endpoints.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from loguru import logger

from .config.settings import SettingsSchema, get_settings_path
from .domain.events import EventBus, ExecutionCompleted, ActionChanged, SettingsChanged
from .domain.types import ActionId
from .domain.result import Err
from .domain.action_catalog import ActionCatalogService
from .application.provider_registry import ProviderRegistry
from .application.pipeline import ExecutionPipeline
from .application.handlers import HistoryRecorder, ActionSync, SettingsPersister
from .infrastructure.secrets import KeyringSecretStore
from .infrastructure.clipboard import ClipboardManager
from .infrastructure.history import HistoryRepository
from .infrastructure.actions import ActionAgent

# Provider registration imports
from .infrastructure.providers.base import register_openai, register_openai_compatible, register_mock
from .infrastructure.providers.anthropic import register_anthropic
from .infrastructure.providers.google import register_google
from .infrastructure.providers.mistral import register_mistral
from .infrastructure.providers.tesseract import register_tesseract


@dataclass
class AppServices:
    """Container for all application services."""
    settings: SettingsSchema
    settings_file: Path
    secret_store: KeyringSecretStore
    clipboard: ClipboardManager
    history_repo: HistoryRepository
    provider_registry: ProviderRegistry
    pipeline: ExecutionPipeline
    action_catalog: ActionCatalogService
    action_agent: ActionAgent
    event_bus: EventBus


def create_services() -> AppServices:
    """Wire all services. Called once at startup."""

    # 1. Core infrastructure
    settings_file = get_settings_path()
    settings = SettingsSchema.load(settings_file)
    secret_store = KeyringSecretStore()
    clipboard = ClipboardManager()

    # 2. Repositories
    base_dir = Path(__file__).resolve().parent.parent  # Points to backend/
    history_repo = HistoryRepository(base_dir / "history.json")
    action_catalog = ActionCatalogService(base_dir / "actions.json")

    # 3. Provider Registry
    registry = ProviderRegistry()
    register_openai(registry)
    register_openai_compatible(registry)
    register_anthropic(registry)
    register_google(registry)
    register_mistral(registry)
    register_tesseract(registry)
    register_mock(registry)

    # 4. Event Bus
    event_bus = EventBus()

    # 5. Application services
    pipeline = ExecutionPipeline(settings, secret_store, clipboard, registry, event_bus)

    # 6. Background services
    def on_action_trigger(action_id: Optional[str] = None):
        """Callback for global hotkeys. Runs in a background thread."""
        logger.debug(f"Action trigger received: {action_id}")
        if action_id:
            try:
                action = action_catalog.get(ActionId(action_id))
                if not action:
                    logger.warning(f"Action not found for trigger: {action_id}")
                    return

                result = pipeline.execute(action)
                if isinstance(result, Err):
                    logger.warning(f"Action {action_id} validation failed: {result.error.message}")
                    return

                chunks = list(result.value)
                logger.info(f"Action {action_id} executed successfully: {len(''.join(chunks))} chars")
            except Exception as e:
                logger.error(f"Failed to execute action {action_id}: {e}")

    action_agent = ActionAgent(on_trigger=on_action_trigger)

    # 7. Wire event handlers
    history_handler = HistoryRecorder(history_repo, settings)
    event_bus.subscribe(ExecutionCompleted, history_handler.handle)

    action_sync = ActionSync(action_agent, action_catalog)
    event_bus.subscribe(ActionChanged, action_sync.handle)

    settings_persister = SettingsPersister(settings, settings_file)
    event_bus.subscribe(SettingsChanged, settings_persister.handle)

    return AppServices(
        settings=settings,
        settings_file=settings_file,
        secret_store=secret_store,
        clipboard=clipboard,
        history_repo=history_repo,
        provider_registry=registry,
        pipeline=pipeline,
        action_catalog=action_catalog,
        action_agent=action_agent,
        event_bus=event_bus,
    )
