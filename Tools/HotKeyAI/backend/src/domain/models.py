from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal, Dict, Union
from datetime import datetime
import uuid

from .types import ConnectionId, ActionId, ProviderId

# --- Core Enums & Types ---

CapabilityType = Literal['stt', 'llm', 'ocr', 'embedding', 'tts']
ProviderClass = Literal['cloud', 'local']
ActionMode = Literal['ai_transform', 'local_transform', 'static_text_paste', 'prompt_prefill_only']
ActionKind = Literal['builtin', 'custom', 'user']
ModelSource = Literal['curated', 'custom']

# --- Provider Catalog Models ---

class ModelDefinition(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    provider_id: ProviderId
    capabilities: List[CapabilityType]
    model_id: str
    status: Literal['active', 'deprecated', 'beta'] = 'active'
    source: ModelSource = 'curated'
    description: Optional[str] = None

class ProviderDefinition(BaseModel):
    provider_id: ProviderId
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
    connection_id: ConnectionId = Field(default_factory=lambda: ConnectionId(str(uuid.uuid4())))
    provider_id: ProviderId
    capabilities: List[CapabilityType]
    model_id: str
    model_source: ModelSource = 'curated'

    # Configuration
    endpoint_url: Optional[str] = None
    deployment_alias: Optional[str] = None
    system_prompt: Optional[str] = None # For LLM
    transcription_hint: Optional[str] = None # For STT

    # State
    is_healthy: bool = False
    last_health_check: Optional[datetime] = None
    secret_ref: Optional[str] = None  # Reference to secret store items (not the secret itself)
    endpoint: Optional[str] = None  # Override endpoint for custom providers

# --- Action Catalog Models ---

class CapabilityRequirement(BaseModel):
    capability: CapabilityType
    min_sequence: int = 0

class InputRequirement(BaseModel):
    type: Literal['text', 'image', 'audio_stream', 'audio_file', 'file_ref']

class LocalTransformConfig(BaseModel):
    type: Literal['regex', 'sed']
    pattern: str
    replacement: str

class ActionDefinition(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    id: ActionId = Field(default_factory=lambda: ActionId(str(uuid.uuid4())))
    kind: ActionKind
    mode: ActionMode

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
    llm_connection_id: Optional[ConnectionId] = None
    stt_connection_id: Optional[ConnectionId] = None

    # Configuration
    prompt_template: Optional[str] = None
    static_text_template: Optional[str] = None
    local_transform_config: Optional[LocalTransformConfig] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ActionCatalog(BaseModel):
    catalog_version: int = 1
    actions: List[ActionDefinition] = []


# --- API Response Models (for OpenAPI schema generation) ---

class ProviderInfoResponse(BaseModel):
    provider_id: str
    display_name: str
    capabilities: List[str]
    requires_auth: bool
    provider_class: str

class HealthResponse(BaseModel):
    status: str
    version: str

class ExecuteResponse(BaseModel):
    result: str

class StatusResponse(BaseModel):
    status: str

class SessionTokenResponse(BaseModel):
    token: str

class HistoryEntryResponse(BaseModel):
    action_id: str
    timestamp: float
    duration: float
    input_preview: str
    output_preview: str
    model_id: str
    status: str
