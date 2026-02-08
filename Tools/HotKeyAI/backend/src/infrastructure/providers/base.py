from abc import ABC, abstractmethod
from typing import Iterator, List, Optional, Dict, Any, Union
from pydantic import BaseModel
from openai import OpenAI
import os

class Message(BaseModel):
    role: str
    content: str

class StreamChunk(BaseModel):
    content: str
    done: bool = False

class ProviderConfig(BaseModel):
    model_id: str
    api_key: str
    endpoint_url: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7

class IProvider(ABC):
    @abstractmethod
    def stream_chat(self, messages: List[Message], config: ProviderConfig) -> Iterator[StreamChunk]:
        pass

class OpenAIProvider(IProvider):
    def stream_chat(self, messages: List[Message], config: ProviderConfig) -> Iterator[StreamChunk]:
        client = OpenAI(
            api_key=config.api_key,
            base_url=config.endpoint_url # Optional, supports compatible endpoints (e.g. LocalAI, vLLM)
        )
        
        # Prepare messages: inject system prompt if not present? 
        # Usually pipeline handles system prompt injection. 
        # Here we just pass what we get, but if config has system prompt 
        # and messages don't start with it, we might prepend.
        # Design decision: Pipeline constructs full message list including system.
        
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        
        try:
            stream = client.chat.completions.create(
                model=config.model_id,
                messages=formatted_messages,
                temperature=config.temperature,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield StreamChunk(content=chunk.choices[0].delta.content)
            
            yield StreamChunk(content="", done=True)
            
        except Exception as e:
            # Propagate error as a special chunk or raise?
            # Raising allows Pipeline to catch and show "Connection Error" in UI
            raise e

class MockProvider(IProvider):
    def stream_chat(self, messages: List[Message], config: ProviderConfig) -> Iterator[StreamChunk]:
        dummy_response = "This is a mock response from HotKeyAI. "
        for word in dummy_response.split():
            yield StreamChunk(content=word + " ")
            import time; time.sleep(0.05)
        yield StreamChunk(content="", done=True)
