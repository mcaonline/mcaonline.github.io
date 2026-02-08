from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, List, Optional
import json
import os
from pathlib import Path

class MainTriggerConfig(BaseModel):
    chord: str = "Ctrl+V,V"
    second_v_timeout_ms: int = 500

class HotkeysConfig(BaseModel):
    main_trigger: MainTriggerConfig = Field(default_factory=MainTriggerConfig)
    # catalog will be loaded from HotkeyCatalog SSoT, not duplicated here in full
    # but we might store overrides or simple enabled states here if needed.
    # For now, following SSoT, the catalog file is separate.

class RoutingDefaults(BaseModel):
    default_stt_connection_id: Optional[str] = None
    default_llm_connection_id: Optional[str] = None

class HistoryConfig(BaseModel):
    enabled: bool = False
    max_entries: int = 10

class PrivacyConfig(BaseModel):
    trust_notice_ack_for_direct_ai: bool = False

class DiagnosticsConfig(BaseModel):
    debug_payload_logging: bool = False

class AppConfig(BaseModel):
    theme: str = "system"
    language: str = "en"

class SettingsSchema(BaseSettings):
    schema_version: int = 1
    app: AppConfig = Field(default_factory=AppConfig)
    hotkeys: HotkeysConfig = Field(default_factory=HotkeysConfig)
    routing_defaults: RoutingDefaults = Field(default_factory=RoutingDefaults)
    history: HistoryConfig = Field(default_factory=HistoryConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    diagnostics: DiagnosticsConfig = Field(default_factory=DiagnosticsConfig)
    
    # Store Connection Metadta (Not secrets)
    connections: List[Dict] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_prefix="HOTKEYAI_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )

    def save(self, path: Path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: Path) -> "SettingsSchema":
        if not path.exists():
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.model_validate(data)
        except Exception as e:
            # Fallback to defaults on error, or re-raise depending on policy
            print(f"Error loading settings: {e}")
            return cls()

# Global settings instance
SETTINGS_FILE = Path("settings.json")
settings = SettingsSchema.load(SETTINGS_FILE)
