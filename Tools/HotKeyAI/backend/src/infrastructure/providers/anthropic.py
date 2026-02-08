import httpx
from typing import Iterator, List
from .base import IProvider, Message, StreamChunk, ProviderConfig
import json

class AnthropicProvider(IProvider):
    def stream_chat(self, messages: List[Message], config: ProviderConfig) -> Iterator[StreamChunk]:
        """Implementation for Anthropic Claude API."""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Anthropic likes a specific role mapping
        formatted_messages = []
        for m in messages:
            role = "user" if m.role == "user" else "assistant"
            formatted_messages.append({"role": role, "content": m.content})

        data = {
            "model": config.model_id,
            "messages": formatted_messages,
            "system": config.system_prompt or "",
            "max_tokens": 4096,
            "stream": True
        }

        try:
            with httpx.stream("POST", url, headers=headers, json=data, timeout=60.0) as response:
                if response.status_code != 200:
                    error_detail = response.read().decode()
                    raise Exception(f"Anthropic API Error ({response.status_code}): {error_detail}")
                
                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    
                    line_content = line[6:]
                    if line_content == "[DONE]":
                        break
                        
                    try:
                        event = json.loads(line_content)
                        event_type = event.get("type")
                        
                        if event_type == "content_block_delta":
                            delta = event.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield StreamChunk(content=delta.get("text", ""))
                        elif event_type == "message_stop":
                            yield StreamChunk(content="", done=True)
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            raise Exception(f"Anthropic connection failed: {str(e)}")
