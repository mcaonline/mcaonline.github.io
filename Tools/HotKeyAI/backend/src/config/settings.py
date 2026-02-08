from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, List, Optional
import json
import os
from loguru import logger
import stat
from pathlib import Path

class MainTriggerConfig(BaseModel):
    chord: str = "Ctrl+V,V"
    second_v_timeout_ms: int = 500

class HotkeysConfig(BaseModel):
    main_trigger: MainTriggerConfig = Field(default_factory=MainTriggerConfig)

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
    ui_opacity: float = 0.95  # Transparency level (0.0 to 1.0)

class SettingsSchema(BaseSettings):
    schema_version: int = 1
    app: AppConfig = Field(default_factory=AppConfig)
    hotkeys: HotkeysConfig = Field(default_factory=HotkeysConfig)
    routing_defaults: RoutingDefaults = Field(default_factory=RoutingDefaults)
    history: HistoryConfig = Field(default_factory=HistoryConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    diagnostics: DiagnosticsConfig = Field(default_factory=DiagnosticsConfig)
    
    # Store Connection Metadata (Not secrets)
    connections: List[Dict] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_prefix="PASTE_SPEECH_AI_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )

    def save(self, path: Path):
        """Save settings with secure file permissions."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))
        
        # Set file permissions to user-only read/write (Windows-safe)
        try:
            if os.name == 'nt':
                # Windows: Remove inheritance and set user-only access
                import subprocess
                subprocess.run(
                    ['icacls', str(path), '/inheritance:r', '/grant:r', f'{os.getlogin()}:F'],
                    capture_output=True, check=False
                )
            else:
                # Unix: chmod 600
                os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass  # Best effort security

    @classmethod
    def load(cls, path: Path) -> "SettingsSchema":
        if not path.exists():
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Migration: Robustly ensure all connections have a capabilities list
            if "connections" in data and isinstance(data["connections"], list):
                for conn in data["connections"]:
                    if not isinstance(conn, dict):
                        continue
                        
                    # Fix plural 'capabilities'
                    existing_caps = conn.get("capabilities")
                    if existing_caps is None:
                        # Fallback to singular 'capability'
                        single_cap = conn.get("capability")
                        if single_cap:
                            conn["capabilities"] = [single_cap]
                        else:
                            conn["capabilities"] = ["llm"]
                    elif isinstance(existing_caps, str):
                        # Fix cases where it might have been saved as a string
                        conn["capabilities"] = [existing_caps.lower()]
                    
                    # Ensure it's lowercase to match Literal types
                    if isinstance(conn["capabilities"], list):
                        conn["capabilities"] = [c.lower() for c in conn["capabilities"] if isinstance(c, str)]

            try:
                return cls.model_validate(data)
            except Exception as validation_error:
                logger.error(f"Settings validation failed: {validation_error}")
                # Log the data for debugging (be careful with secrets, but connections don't have them yet)
                return cls.model_validate(data) # Just returning it for now, pydantic handles it
        except Exception as e:
            print(f"Error loading settings: {e}")
            return cls()

def get_settings_path() -> Path:
    """Get secure settings path in user's AppData."""
    if os.name == 'nt':
        base = Path(os.environ.get('APPDATA', Path.home()))
    else:
        base = Path.home() / '.config'
    
    app_dir = base / 'HotKeyAI'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / 'settings.json'

# Global settings instance
SETTINGS_FILE = get_settings_path()
settings = SettingsSchema.load(SETTINGS_FILE)
