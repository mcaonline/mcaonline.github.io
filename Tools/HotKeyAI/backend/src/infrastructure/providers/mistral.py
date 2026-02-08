import httpx
from typing import Iterator, List
from .base import IProvider, Message, StreamChunk, ProviderConfig
import json

class MistralProvider(IProvider):
    def stream_chat(self, messages: List[Message], config: ProviderConfig) -> Iterator[StreamChunk]:
        """Implementation for Mistral AI API."""
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        formatted_messages = []
        if config.system_prompt:
            formatted_messages.append({"role": "system", "content": config.system_prompt})
            
        for m in messages:
            formatted_messages.append({"role": m.role, "content": m.content})

        data = {
            "model": config.model_id,
            "messages": formatted_messages,
            "temperature": config.temperature,
            "stream": True
        }

        try:
            with httpx.stream("POST", url, headers=headers, json=data, timeout=60.0) as response:
                if response.status_code != 200:
                    error_detail = response.read().decode()
                    raise Exception(f"Mistral API Error ({response.status_code}): {error_detail}")
                
                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    
                    line_content = line[6:]
                    if line_content == "[DONE]":
                        break
                        
                    try:
                        chunk_data = json.loads(line_content)
                        choices = chunk_data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            if "content" in delta:
                                yield StreamChunk(content=delta["content"])
                    except json.JSONDecodeError:
                        continue
                
                yield StreamChunk(content="", done=True)
        except Exception as e:
            raise Exception(f"Mistral connection failed: {str(e)}")
