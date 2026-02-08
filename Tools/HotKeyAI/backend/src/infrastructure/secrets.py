from abc import ABC, abstractmethod
from typing import List, Optional, Dict
import keyring
from pydantic import BaseModel
from loguru import logger

from ..domain.types import ConnectionId

class SecretMetadata(BaseModel):
    connection_id: ConnectionId
    service_category: str
    account_name: str

class ISecretStore(ABC):
    @abstractmethod
    def save(self, connection_id: ConnectionId, service_category: str, secret_value: str) -> None:
        pass

    @abstractmethod
    def read(self, connection_id: ConnectionId, service_category: str) -> Optional[str]:
        pass

    @abstractmethod
    def delete(self, connection_id: ConnectionId, service_category: str) -> None:
        pass

    @abstractmethod
    def list_references(self) -> List[SecretMetadata]:
        pass

class KeyringSecretStore(ISecretStore):
    """
    Implementation of ISecretStore using the system keyring service.
    On Windows, this targets Windows Credential Manager.
    """
    from ..domain.app_constants import SERVICE_NAME

    def _get_account_name(self, connection_id: ConnectionId, service_category: str) -> str:
        return f"{connection_id}::{service_category}"

    def save(self, connection_id: ConnectionId, service_category: str, secret_value: str) -> None:
        account_name = self._get_account_name(connection_id, service_category)
        keyring.set_password(self.SERVICE_NAME, account_name, secret_value)

    def read(self, connection_id: ConnectionId, service_category: str) -> Optional[str]:
        account_name = self._get_account_name(connection_id, service_category)
        return keyring.get_password(self.SERVICE_NAME, account_name)

    def delete(self, connection_id: ConnectionId, service_category: str) -> None:
        account_name = self._get_account_name(connection_id, service_category)
        try:
            keyring.delete_password(self.SERVICE_NAME, account_name)
        except keyring.errors.PasswordDeleteError:
            # Metadata might exist but secret was already gone or never existed
            pass
        except Exception as e:
            logger.warning(f"Failed to delete secret for {account_name}: {e}")

    def list_references(self) -> List[SecretMetadata]:
        # NOTE: 'keyring' library does not standardly support listing all credentials 
        # for a specific service name across all backends.
        # For a strict implementation on Windows, we might need `win32cred` via `pywin32` 
        # or `ctypes` to enumerate credentials if this feature is required for UI.
        #
        # For now, we return an empty list or we would need to maintain a separate
        # non-secret index of what secrets we HAVE stored in Settings.
        # The design says: "list_references() -> metadata[] (metadata only; never secret values)"
        #
        # Recommendation: The app `Settings` (connections list) is the source of truth for 
        # "what connections exist". The SecretStore is just a dumb vault. 
        # We don't necessarily need to enumerate the vault to know what we have; 
        # we check the Settings `connections` list and try to read the secret for each.
        return []

# Singleton instance
secret_store = KeyringSecretStore()
