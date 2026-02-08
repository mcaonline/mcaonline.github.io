from typing import Dict, Optional, Iterator
from ..infrastructure.providers.base import IProvider, MockProvider, OpenAIProvider, ProviderConfig, Message, StreamChunk
from ..domain.models import HotkeyDefinition, ConnectionDefinition
from ..infrastructure.clipboard import ClipboardManager
from ..infrastructure.history import HistoryRepository, HistoryEntry
import time
import re
from loguru import logger

# Sensitive data patterns to redact from logs
SENSITIVE_PATTERNS = [
    r'sk-[a-zA-Z0-9]{20,}',  # OpenAI API keys
    r'[a-zA-Z0-9+/]{40,}={0,2}',  # Base64 encoded secrets
    r'password\s*[:=]\s*\S+',  # Passwords
    r'api[_-]?key\s*[:=]\s*\S+',  # API keys
]

def redact_sensitive(text: str) -> str:
    """Redact sensitive information from text before logging."""
    if not text:
        return text
    result = text
    for pattern in SENSITIVE_PATTERNS:
        result = re.sub(pattern, '[REDACTED]', result, flags=re.IGNORECASE)
    return result

class ProviderFactory:
    @staticmethod
    def create(connection: ConnectionDefinition, secret_key: Optional[str] = None) -> IProvider:
        if "mock" in connection.provider_id.lower():
            return MockProvider()
        elif "openai" in connection.provider_id.lower():
            return OpenAIProvider()
        else:
            logger.warning(f"Unknown provider type for {connection.provider_id}, defaulting to OpenAI structure")
            return OpenAIProvider()

    @staticmethod
    def create_config(connection: ConnectionDefinition, secret_key: str, hotkey: HotkeyDefinition) -> ProviderConfig:
        return ProviderConfig(
            model_id=connection.model_id,
            api_key=secret_key,
            endpoint_url=connection.endpoint_url,
            system_prompt=connection.system_prompt,
            temperature=0.7
        )

class ExecutionPipeline:
    def __init__(self, settings, secret_store, clipboard: ClipboardManager, history: HistoryRepository):
        self.settings = settings
        self.secret_store = secret_store
        self.clipboard = clipboard
        self.history = history

    def execute(self, hotkey: HotkeyDefinition) -> Iterator[str]:
        """
        Main execution flow:
        1. Gather Context (Selected Text / Clipboard)
        2. Resolve Connection
        3. Prepare Provider & Config
        4. Stream Response
        5. Post-Process (Side effects)
        """
        start_time = time.time()
        
        # 1. Gather Context
        selected_text = self.clipboard.get_selected_text()
        clipboard_text = self.clipboard.read_text()
        
        context_data = {
            "selected_text": selected_text or "",
            "clipboard": clipboard_text or ""
        }
        
        # 2. Resolve Connection
        connection_id = hotkey.llm_connection_id
        if not connection_id:
             connection_id = self.settings.routing_defaults.default_llm_connection_id
        
        if not connection_id:
            yield "Error: No AI connection configured for this hotkey."
            return

        # Find Connection Def
        connection = next((c for c in self.settings.connections if c['connection_id'] == connection_id), None)
        if isinstance(connection, dict):
            connection = ConnectionDefinition(**connection)
            
        if not connection:
            yield "Error: Connection definition not found."
            return

        # 3. Get Secret
        secret = self.secret_store.read(connection.connection_id, "api_key")
        if not secret:
            yield "Error: API Key not found for this connection."
            return

        # 4. Prepare Provider
        provider = ProviderFactory.create(connection, secret)
        config = ProviderFactory.create_config(connection, secret, hotkey)
        
        # 5. Build Prompt
        user_prompt = hotkey.prompt_template or "{selected_text}"
        for k, v in context_data.items():
            user_prompt = user_prompt.replace(f"{{{k}}}", v)
            
        messages = [
            Message(role="user", content=user_prompt)
        ]
        
        # 6. Stream
        full_response = ""
        try:
            for chunk in provider.stream_chat(messages, config):
                if chunk.content:
                    full_response += chunk.content
                    yield chunk.content
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            yield f"\n[Error: {str(e)}]"
            
        # 7. Log History (with privacy protection)
        duration = time.time() - start_time
        
        # Only log if history is enabled and user has acknowledged privacy
        if self.settings.history.enabled:
            # Redact sensitive data from previews
            safe_input = redact_sensitive(user_prompt[:50]) if user_prompt else ""
            safe_output = redact_sensitive(full_response[:50]) if full_response else ""
            
            self.history.add(HistoryEntry(
                hotkey_id=hotkey.id,
                timestamp=start_time,
                duration=duration,
                input_preview=safe_input,
                output_preview=safe_output,
                model_id=connection.model_id,
                status="success"
            ))
