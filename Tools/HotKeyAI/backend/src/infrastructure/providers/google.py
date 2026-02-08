import httpx
from typing import Iterator, List
from src.infrastructure.providers.base import IProvider, Message, StreamChunk, ProviderConfig
import json

class GoogleProvider(IProvider):
    def stream_chat(self, messages: List[Message], config: ProviderConfig) -> Iterator[StreamChunk]:
        """Implementation for Google Gemini API."""
        # Note: Using the REST API for Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.model_id}:streamGenerateContent?key={config.api_key}"
        
        # Gemini messages structure
        contents = []
        for m in messages:
            role = "user" if m.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        data = {
            "contents": contents,
            "generationConfig": {
                "temperature": config.temperature,
                "maxOutputTokens": 4096,
            }
        }
        
        if config.system_prompt:
            data["system_instruction"] = {"parts": [{"text": config.system_prompt}]}

        try:
            with httpx.stream("POST", url, json=data, timeout=60.0) as response:
                if response.status_code != 200:
                    error_detail = response.read().decode()
                    raise Exception(f"Google API Error ({response.status_code}): {error_detail}")
                
                # Gemini returns a JSON array of objects, one per chunk, but streamed line by line
                # with potential [ and , characters.
                for line in response.iter_lines():
                    line = line.strip()
                    if not line or line in ("[", "]", ","):
                        continue
                    
                    # Remove trailing comma if present in the stream
                    if line.endswith(","):
                        line = line[:-1]
                        
                    try:
                        chunk_data = json.loads(line)
                        candidates = chunk_data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                if "text" in part:
                                    yield StreamChunk(content=part["text"])
                    except json.JSONDecodeError:
                        continue
                
                yield StreamChunk(content="", done=True)
        except Exception as e:
            raise Exception(f"Google Gemini connection failed: {str(e)}")
