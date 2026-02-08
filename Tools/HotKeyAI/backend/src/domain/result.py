"""
Result type for structured error handling.

Pipeline returns Result[Iterator[str]] instead of embedding errors as
yield "Error:..." strings. Callers use isinstance checks:

    result = pipeline.execute(action)
    if isinstance(result, Err):
        # handle result.error (a PipelineError)
    else:
        # stream from result.value
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, TypeVar, Union, Generic

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    value: T

    @property
    def is_ok(self) -> bool:
        return True

    @property
    def is_err(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class Err:
    error: Any  # PipelineError at runtime; Any to avoid circular imports

    @property
    def is_ok(self) -> bool:
        return False

    @property
    def is_err(self) -> bool:
        return True


Result = Union[Ok[T], Err]
