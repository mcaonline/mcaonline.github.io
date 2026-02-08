"""
Value Objects for domain IDs.

NewType provides compile-time type safety with zero runtime overhead.
Pydantic v2 serializes NewType as the base type (str), so JSON API is unchanged.
"""

from typing import NewType

ConnectionId = NewType("ConnectionId", str)
ActionId = NewType("ActionId", str)
ProviderId = NewType("ProviderId", str)
