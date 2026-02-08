from typing import Dict, Optional, Iterator
from ..infrastructure.providers.base import IProvider, MockProvider, OpenAIProvider, ProviderConfig, Message, StreamChunk
from ..domain.models import HotkeyDefinition, ConnectionDefinition
from ..infrastructure.clipboard import ClipboardManager
from ..infrastructure.history import HistoryRepository, HistoryEntry
import time
import re
from loguru import logger
from ..infrastructure.providers.anthropic import AnthropicProvider
from ..infrastructure.providers.google import GoogleProvider
from ..infrastructure.providers.mistral import MistralProvider
from ..infrastructure.providers.tesseract import TesseractProvider

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
        p_id = connection.provider_id.lower()
        if "mock" in p_id:
            return MockProvider()
        elif "openai" in p_id and "oss" not in p_id:
            return OpenAIProvider()
        elif "anthropic" in p_id:
            return AnthropicProvider()
        elif "google" in p_id:
            return GoogleProvider()
        elif "mistral" in p_id:
            return MistralProvider()
        elif "groq" in p_id or "ollama" in p_id or "oss" in p_id:
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
        self.tesseract = TesseractProvider()

    def execute(self, hotkey: HotkeyDefinition) -> Iterator[str]:
        """
        Main execution flow:
        1. Gather Context (Text / Image / Audio)
        2. Resolve Connection
        3. Prepare Provider & Config
        4. Stream Response
        5. Post-Process (Side effects)
        """
        start_time = time.time()
        
        # 1. Gather Context
        context_data = {
            "selected_text": self.clipboard.get_selected_text() or "",
            "clipboard": self.clipboard.read_text() or ""
        }
        
        # Handle OCR Requirement
        if hotkey.mode == 'ai_transform' and any(r.capability == 'ocr' for r in hotkey.capability_requirements):
            image = self.clipboard.read_image()
            if image:
                logger.info("OCR Mode: Running Tesseract...")
                ocr_text = self.tesseract.process_image(image)
                context_data["ocr_text"] = ocr_text
                # Merge into selected_text if not explicitly templated
                if "{ocr_text}" not in (hotkey.prompt_template or ""):
                    context_data["selected_text"] = ocr_text
            else:
                yield "Error: OCR triggered but no image found in clipboard."
                return

        # 2. Resolve Connection
        if hotkey.mode == 'local_transform':
            config = hotkey.local_transform_config or {}
            transform_type = config.get('type', 'regex') if isinstance(config, dict) else 'regex'
            
            if transform_type == 'regex':
                source = context_data['selected_text'] or context_data['clipboard']
                yield source
            else:
                yield f"Error: Unknown local transform type {transform_type}"
            return

        connection_id = hotkey.llm_connection_id
        if not connection_id:
             connection_id = self.settings.routing_defaults.default_llm_connection_id
        
        if not connection_id:
            yield "Error: No AI connection configured for this hotkey."
            return

        connection_dict = next((c for c in self.settings.connections if c['connection_id'] == connection_id), None)
        if not connection_dict:
            yield "Error: Connection definition not found."
            return
            
        # Migration check: if old data only has 'capability', convert to 'capabilities'
        if 'capability' in connection_dict and 'capabilities' not in connection_dict:
            connection_dict['capabilities'] = [connection_dict.pop('capability')]
        
        connection = ConnectionDefinition(**connection_dict)

        # Check if connection supports all required capabilities
        for req in hotkey.capability_requirements:
            if req.capability not in connection.capabilities:
                yield f"Error: Connection '{connection.connection_id}' does not support required capability '{req.capability}'."
                return

        # 3. Get Secret
        secret = self.secret_store.read(connection.connection_id, "api_key")
        # Ollama/Local might not need secret
        is_local = any(x in connection.provider_id.lower() for x in ['ollama', 'tesseract', 'oss', 'mock'])
        if not secret and not is_local:
            yield "Error: API Key missing for this connection."
            return

        # 4. Prepare Provider
        provider = ProviderFactory.create(connection, secret)
        config = ProviderFactory.create_config(connection, secret or "", hotkey)
        
        # 5. Build Prompt
        user_prompt = hotkey.prompt_template or "{selected_text}"
        for k, v in context_data.items():
            user_prompt = user_prompt.replace(f"{{{k}}}", str(v))
            
        messages = [
            Message(role="user", content=user_prompt)
        ]
        
        # 6. Stream
        full_response = ""
        try:
            for chunk in provider.stream_chat(messages, config):
                if chunk.content:
                    content_str = str(chunk.content)
                    full_response += content_str
                    yield content_str
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            yield f"\n[Error: {str(e)}]"
            
        # 7. History
        duration = time.time() - start_time
        if self.settings.history.enabled:
            safe_input = redact_sensitive(user_prompt[:50])
            safe_output = redact_sensitive(full_response[:50])
            self.history.add(HistoryEntry(
                hotkey_id=hotkey.id,
                timestamp=start_time,
                duration=duration,
                input_preview=safe_input,
                output_preview=safe_output,
                model_id=connection.model_id,
                status="success"
            ))
