from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal, Dict, Union
from datetime import datetime
import uuid

# --- Core Enums & Types ---

CapabilityType = Literal['stt', 'llm', 'ocr', 'embedding', 'tts']
ProviderClass = Literal['cloud', 'local']
HotkeyMode = Literal['ai_transform', 'local_transform', 'static_text_paste', 'prompt_prefill_only']
HotkeyKind = Literal['builtin', 'custom']
ModelSource = Literal['curated', 'custom']

# --- Provider Catalog Models ---

class ModelDefinition(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    provider_id: str
    capabilities: List[CapabilityType]
    model_id: str
    status: Literal['active', 'deprecated', 'beta'] = 'active'
    source: ModelSource = 'curated'
    description: Optional[str] = None

class ProviderDefinition(BaseModel):
    provider_id: str
    display_name: str
    provider_class: ProviderClass
    capabilities: List[CapabilityType]
    requires_consent: bool = False
    requires_endpoint: bool = False
    requires_auth: bool = True
    terms_url: Optional[str] = None
    privacy_url: Optional[str] = None

class ProviderCatalog(BaseModel):
    catalog_version: str
    providers: List[ProviderDefinition]
    curated_models: List[ModelDefinition]

# --- Connection Models ---

class ConnectionDefinition(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    connection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str
    capabilities: List[CapabilityType]
    model_id: str
    model_source: ModelSource = 'curated'
    
    # Configuration
    endpoint_url: Optional[str] = None
    deployment_alias: Optional[str] = None
    system_prompt: Optional[str] = None # For LLM
    transcription_hint: Optional[str] = None # For STT
    
    # State
    # State
    is_healthy: bool = False
    last_health_check: Optional[datetime] = None
    secret_ref: Optional[str] = None # Reference to secret store items (not the secret itself)
    endpoint: Optional[str] = None # Override endpoint for custom providers
    endpoint: Optional[str] = None

# --- Hotkey Catalog Models ---

class CapabilityRequirement(BaseModel):
    capability: CapabilityType
    min_sequence: int = 0

class InputRequirement(BaseModel):
    type: Literal['text', 'image', 'audio_stream', 'audio_file', 'file_ref']

class LocalTransformConfig(BaseModel):
    type: Literal['regex', 'sed']
    pattern: str
    replacement: str

class HotkeyDefinition(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kind: HotkeyKind
    mode: HotkeyMode
    
    # Display
    display_key: str # Reference to UiTextCatalog
    description_key: str # Reference to UiTextCatalog
    icon: Optional[str] = None
    
    # State
    enabled: bool = False
    sequence: int = 0
    
    # Triggers
    direct_hotkey: Optional[str] = None
    panel_quick_key: Optional[int] = None # 1-9, runtime derived mostly
    
    # Logic
    capability_requirements: List[CapabilityRequirement] = []
    input_requirements: List[InputRequirement] = []
    
    # Binding
    llm_connection_id: Optional[str] = None
    stt_connection_id: Optional[str] = None
    
    # Configuration
    prompt_template: Optional[str] = None
    static_text_template: Optional[str] = None
    local_transform_config: Optional[LocalTransformConfig] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class HotkeyCatalog(BaseModel):
    catalog_version: int = 1
    hotkeys: List[HotkeyDefinition] = []
