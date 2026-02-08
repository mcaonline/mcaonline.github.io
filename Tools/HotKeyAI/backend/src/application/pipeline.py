from dataclasses import dataclass
from typing import Dict, List, Optional, Iterator
from ..infrastructure.providers.base import IProvider, ProviderConfig, Message, StreamChunk
from ..domain.models import ActionDefinition, ConnectionDefinition
from ..domain.types import ConnectionId, ProviderId
from ..domain.result import Ok, Err, Result
from ..domain.errors import PipelineError, ErrorCategory
from ..domain.events import EventBus, ExecutionCompleted
from ..infrastructure.clipboard import ClipboardManager
from .provider_registry import ProviderRegistry
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


@dataclass
class PipelineContext:
    """Validated execution context, ready for streaming."""
    provider: IProvider
    config: ProviderConfig
    messages: List[Message]
    connection: ConnectionDefinition
    action: ActionDefinition
    user_prompt: str
    start_time: float


class ExecutionPipeline:
    def __init__(self, settings, secret_store, clipboard: ClipboardManager,
                 provider_registry: ProviderRegistry, event_bus: EventBus):
        self.settings = settings
        self.secret_store = secret_store
        self.clipboard = clipboard
        self.registry = provider_registry
        self.event_bus = event_bus

    def validate(self, action: ActionDefinition) -> Result[PipelineContext]:
        """
        Validate and prepare execution context (steps 1-5).
        Returns Ok(PipelineContext) or Err(PipelineError).
        """
        start_time = time.time()

        # 1. Gather Context
        context_data: Dict[str, str] = {
            "selected_text": self.clipboard.get_selected_text() or "",
            "clipboard": self.clipboard.read_text() or ""
        }

        # Handle OCR Requirement
        if action.mode == 'ai_transform' and any(r.capability == 'ocr' for r in action.capability_requirements):
            image = self.clipboard.read_image()
            if image:
                logger.info("OCR Mode: Running Tesseract...")
                ocr_provider = self.registry.create_provider(ProviderId("tesseract"))
                ocr_text = ocr_provider.process_image(image)
                context_data["ocr_text"] = ocr_text
                if "{ocr_text}" not in (action.prompt_template or ""):
                    context_data["selected_text"] = ocr_text
            else:
                return Err(PipelineError(
                    ErrorCategory.MISSING_INPUT,
                    "OCR triggered but no image found in clipboard."
                ))

        # 2. Local Transform (no connection needed)
        if action.mode == 'local_transform':
            config_data = action.local_transform_config or {}
            transform_type = config_data.get('type', 'regex') if isinstance(config_data, dict) else 'regex'

            if transform_type == 'regex':
                source = context_data['selected_text'] or context_data['clipboard']
                # Return a trivial PipelineContext that _stream will handle
                return Ok(PipelineContext(
                    provider=None,  # type: ignore[arg-type]
                    config=None,  # type: ignore[arg-type]
                    messages=[],
                    connection=None,  # type: ignore[arg-type]
                    action=action,
                    user_prompt=source,
                    start_time=start_time,
                ))
            else:
                return Err(PipelineError(
                    ErrorCategory.MISSING_CONFIG,
                    f"Unknown local transform type: {transform_type}"
                ))

        # 3. Resolve Connection
        connection_id = action.llm_connection_id
        if not connection_id:
            connection_id = self.settings.routing_defaults.default_llm_connection_id

        if not connection_id:
            return Err(PipelineError(
                ErrorCategory.MISSING_CONFIG,
                "No AI connection configured for this action."
            ))

        connection_dict = next(
            (c for c in self.settings.connections
             if (c['connection_id'] if isinstance(c, dict) else c.connection_id) == connection_id),
            None
        )
        if not connection_dict:
            return Err(PipelineError(
                ErrorCategory.MISSING_CONFIG,
                "Connection definition not found.",
                connection_id=ConnectionId(connection_id),
            ))

        # Migration check: if old data only has 'capability', convert to 'capabilities'
        if isinstance(connection_dict, dict):
            if 'capability' in connection_dict and 'capabilities' not in connection_dict:
                connection_dict['capabilities'] = [connection_dict.pop('capability')]
            connection = ConnectionDefinition(**connection_dict)
        else:
            connection = connection_dict

        # Check capabilities
        for req in action.capability_requirements:
            if req.capability not in connection.capabilities:
                return Err(PipelineError(
                    ErrorCategory.CAPABILITY_MISMATCH,
                    f"Connection '{connection.connection_id}' does not support required capability '{req.capability}'.",
                    connection_id=connection.connection_id,
                    provider_id=connection.provider_id,
                ))

        # 4. Get Secret
        secret = self.secret_store.read(connection.connection_id, "api_key")
        reg = self.registry.get(connection.provider_id)
        requires_auth = reg.requires_auth if reg else True
        if not secret and requires_auth:
            return Err(PipelineError(
                ErrorCategory.AUTH_MISSING,
                "API Key missing for this connection.",
                connection_id=connection.connection_id,
                provider_id=connection.provider_id,
            ))

        # 5. Prepare Provider + Prompt
        provider = self.registry.create_provider(connection.provider_id)
        provider_config = ProviderConfig(
            model_id=connection.model_id,
            api_key=secret or "",
            endpoint_url=connection.endpoint_url,
            system_prompt=connection.system_prompt,
            temperature=0.7
        )

        user_prompt = action.prompt_template or "{selected_text}"
        for k, v in context_data.items():
            user_prompt = user_prompt.replace(f"{{{k}}}", str(v))

        messages = [Message(role="user", content=user_prompt)]

        return Ok(PipelineContext(
            provider=provider,
            config=provider_config,
            messages=messages,
            connection=connection,
            action=action,
            user_prompt=user_prompt,
            start_time=start_time,
        ))

    def execute(self, action: ActionDefinition) -> Result[Iterator[str]]:
        """
        Main execution flow. Returns Ok(stream) or Err(PipelineError).
        """
        result = self.validate(action)
        if isinstance(result, Err):
            return result
        ctx = result.value

        # Local transform: return text directly
        if action.mode == 'local_transform':
            return Ok(iter([ctx.user_prompt]))

        return Ok(self._stream(ctx))

    def _stream(self, ctx: PipelineContext) -> Iterator[str]:
        """Stream response from provider. Publishes ExecutionCompleted event after."""
        full_response = ""
        status = "success"
        try:
            for chunk in ctx.provider.stream_chat(ctx.messages, ctx.config):
                if chunk.content:
                    content_str = str(chunk.content)
                    full_response += content_str
                    yield content_str
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            status = "error"
            yield f"\n[Error: {str(e)}]"

        duration = time.time() - ctx.start_time
        self.event_bus.publish(ExecutionCompleted(
            action_id=ctx.action.id,
            connection_id=ctx.connection.connection_id,
            model_id=ctx.connection.model_id,
            duration=duration,
            input_preview=ctx.user_prompt[:50],
            output_preview=full_response[:50],
            status=status,
        ))
