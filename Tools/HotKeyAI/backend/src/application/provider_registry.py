"""
Provider Registry — self-registration pattern for provider adapters.

Each provider adapter calls registry.register() with its metadata.
Pipeline resolves providers via registry lookup, never string matching.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from ..domain.types import ProviderId
from ..infrastructure.providers.base import IProvider


@dataclass(frozen=True)
class ProviderRegistration:
    provider_id: ProviderId
    display_name: str
    capabilities: List[str]
    requires_auth: bool = True
    provider_class: str = "cloud"  # "cloud" | "local"
    factory: Callable[[], IProvider] = field(default=None)  # type: ignore[assignment]


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[ProviderId, ProviderRegistration] = {}

    def register(self, registration: ProviderRegistration) -> None:
        self._providers[registration.provider_id] = registration

    def get(self, provider_id: ProviderId) -> Optional[ProviderRegistration]:
        return self._providers.get(provider_id)

    def list_all(self) -> List[ProviderRegistration]:
        return list(self._providers.values())

    def create_provider(self, provider_id: ProviderId) -> IProvider:
        reg = self._providers.get(provider_id)
        if reg is None:
            raise ValueError(f"Unknown provider: {provider_id}")
        return reg.factory()
