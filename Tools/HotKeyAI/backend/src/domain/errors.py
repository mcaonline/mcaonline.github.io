"""
Structured error types for the execution pipeline.

Each PipelineError carries a category (for programmatic handling) and a
human-readable message (for UI display).
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .types import ConnectionId, ProviderId


class ErrorCategory(str, Enum):
    MISSING_INPUT = "missing_input"
    MISSING_CONFIG = "missing_config"
    CAPABILITY_MISMATCH = "capability_mismatch"
    AUTH_MISSING = "auth_missing"
    PROVIDER_ERROR = "provider_error"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PipelineError:
    category: ErrorCategory
    message: str
    connection_id: Optional[ConnectionId] = None
    provider_id: Optional[ProviderId] = None
