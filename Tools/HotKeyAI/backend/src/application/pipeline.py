from typing import Dict, Optional, Iterator
from .providers.base import IProvider, MockProvider, OpenAIProvider, ProviderConfig, Message, StreamChunk
from ..domain.models import HotkeyDefinition, ConnectionDefinition
from .clipboard import ClipboardManager
from .history import HistoryRepository, HistoryEntry
import time
from loguru import logger

class ProviderFactory:
    @staticmethod
    def create(connection: ConnectionDefinition, secret_key: Optional[str] = None) -> IProvider:
        # Check connection.provider_id or capability to decide class
        # Ideally we'd look up ProviderCatalog, but for now we hardcode types
        # connection.provider_id like "openai-gpt4", "mock-provider"
        
        if "mock" in connection.provider_id.lower():
            return MockProvider()
        elif "openai" in connection.provider_id.lower():
            return OpenAIProvider()
        else:
            # Fallback or error
            logger.warning(f"Unknown provider type for {connection.provider_id}, defaulting to OpenAI structure")
            return OpenAIProvider()

    @staticmethod
    def create_config(connection: ConnectionDefinition, secret_key: str, hotkey: HotkeyDefinition) -> ProviderConfig:
        return ProviderConfig(
            model_id=connection.model_id,
            api_key=secret_key,
            endpoint_url=connection.endpoint_url,
            system_prompt=connection.system_prompt,
            temperature=0.7 # Could come from HotkeyDefinition
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
        
        # Validation: check input requirements
        # e.g. input_requirements=['text'] -> if no selected text, fail or fallback?
        # Contract says: "If no selected text -> clipboard is used" (usually)
        # For now, we assume we have what we need or the prompt handles empty strings.
        
        # 2. Resolve Connection
        connection_id = hotkey.llm_connection_id
        if not connection_id:
             # Try default?
             connection_id = self.settings.routing_defaults.default_llm_connection_id
        
        if not connection_id:
            yield "Error: No AI connection configured for this hotkey."
            return

        # Find Connection Def
        connection = next((c for c in self.settings.connections if c['connection_id'] == connection_id), None)
        # Note: SettingsSchema.connections is List[Dict], need to cast or parse? 
        # Models defines ConnectionDefinition.
        if isinstance(connection, dict):
            connection = ConnectionDefinition(**connection)
            
        if not connection:
            yield "Error: Connection definition not found."
            return

        # 3. Get Secret
        # Assuming single secret for now
        secret = self.secret_store.read(connection.connection_id, "api_key")
        if not secret:
            yield "Error: API Key not found for this connection."
            return

        # 4. Prepare Provider
        provider = ProviderFactory.create(connection, secret)
        config = ProviderFactory.create_config(connection, secret, hotkey)
        
        # 5. Build Prompt
        # Simple Jinja-style replacement?
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
            
        # 7. Log History
        duration = time.time() - start_time
        self.history.add(HistoryEntry(
            hotkey_id=hotkey.id,
            timestamp=start_time,
            duration=duration,
            input_preview=user_prompt[:50],
            output_preview=full_response[:50],
            model_id=connection.model_id,
            status="success"
        ))

