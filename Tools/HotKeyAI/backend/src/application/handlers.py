"""
Event handlers — subscribe to domain events, execute side effects.

Wired in the composition root. Each handler is a small class with a
`handle(event)` method.
"""

from pathlib import Path
from loguru import logger

from ..domain.events import ExecutionCompleted, ActionChanged, SettingsChanged
from ..infrastructure.history import HistoryRepository, HistoryEntry


# Re-use the redact function from pipeline
def _redact_sensitive(text: str) -> str:
    import re
    patterns = [
        r'sk-[a-zA-Z0-9]{20,}',
        r'[a-zA-Z0-9+/]{40,}={0,2}',
        r'password\s*[:=]\s*\S+',
        r'api[_-]?key\s*[:=]\s*\S+',
    ]
    result = text
    for pattern in patterns:
        result = re.sub(pattern, '[REDACTED]', result, flags=re.IGNORECASE)
    return result


class HistoryRecorder:
    """Listens to ExecutionCompleted, records to history repository."""

    def __init__(self, history: HistoryRepository, settings) -> None:
        self.history = history
        self.settings = settings

    def handle(self, event: ExecutionCompleted) -> None:
        if not self.settings.history.enabled:
            return
        self.history.add(HistoryEntry(
            action_id=event.action_id,
            timestamp=event.timestamp,
            duration=event.duration,
            input_preview=_redact_sensitive(event.input_preview),
            output_preview=_redact_sensitive(event.output_preview),
            model_id=event.model_id,
            status=event.status,
        ))


class ActionSync:
    """Listens to ActionChanged, updates the global action agent."""

    def __init__(self, action_agent, action_catalog) -> None:
        self.action_agent = action_agent
        self.catalog = action_catalog

    def handle(self, event: ActionChanged) -> None:
        self.action_agent.update_actions(self.catalog.get_all())


class SettingsPersister:
    """Listens to SettingsChanged, saves settings to disk."""

    def __init__(self, settings, settings_file: Path) -> None:
        self.settings = settings
        self.settings_file = settings_file

    def handle(self, event: SettingsChanged) -> None:
        self.settings.save(self.settings_file)
