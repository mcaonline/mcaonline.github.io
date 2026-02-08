"""
Domain Events and synchronous EventBus.

Events decouple side effects (history recording, action sync, settings
persistence) from the code that triggers them. Handlers are registered
in the composition root.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Type
import time
from loguru import logger

from .types import ConnectionId, ActionId


# --- Base Event ---

@dataclass(frozen=True)
class DomainEvent:
    timestamp: float = field(default_factory=time.time)


# --- Concrete Events ---

@dataclass(frozen=True)
class ExecutionCompleted(DomainEvent):
    """Fired after an action execution finishes (success or error)."""
    action_id: ActionId = ActionId("")
    connection_id: ConnectionId = ConnectionId("")
    model_id: str = ""
    duration: float = 0.0
    input_preview: str = ""
    output_preview: str = ""
    status: str = "success"  # "success" | "error"


@dataclass(frozen=True)
class ActionChanged(DomainEvent):
    """Fired after any action CRUD operation."""
    pass


@dataclass(frozen=True)
class ConnectionChanged(DomainEvent):
    """Fired after any connection CRUD operation."""
    connection_id: ConnectionId = ConnectionId("")


@dataclass(frozen=True)
class SettingsChanged(DomainEvent):
    """Fired after settings are modified."""
    pass


# --- EventBus ---

class EventBus:
    """Synchronous publish/subscribe event bus."""

    def __init__(self) -> None:
        self._handlers: Dict[Type[DomainEvent], List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[Any], None]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(type(event), []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler failed for {type(event).__name__}: {e}")
