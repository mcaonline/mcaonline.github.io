from typing import Dict, Optional
from pydantic import BaseModel
from enum import Enum

class UiTextKey(str, Enum):
    # App Metadata
    APP_NAME = "app.name"
    
    # Trust & Connect
    TRUST_NOTICE = "trust.ai_mistakes_notice"
    
    # Consent
    CONSENT_AZURE_REQUIRED = "consent.azure_openai.required"
    CONSENT_OPENAI_REQUIRED = "consent.openai.required"
    CONSENT_MISTRAL_REQUIRED = "consent.mistral.required"
    CONSENT_GOOGLE_REQUIRED = "consent.google.required"
    
    # Legal Titles (Bilingual support placeholders)
    LEGAL_TERMS = "legal.terms_of_use"
    LEGAL_PRIVACY = "legal.privacy_policy"
    LEGAL_MS_PRIVACY = "legal.ms_privacy"
    
    # Errors
    ERR_CONNECTION_REQUIRED = "error.connection_required"
    ERR_AUTH_FAILED = "error.auth_failed"
    ERR_PROVIDER_UNAVAILABLE = "error.provider_unavailable"
    
    # Status
    STATUS_NOT_READY = "status.not_ready"
    STATUS_READY = "status.ready"
    STATUS_DISCONNECTED = "status.disconnected"
    
    # General Labels
    LABEL_HOTKEYS = "label.hotkeys"
    LABEL_SETTINGS = "label.settings"
    LABEL_SAVE = "label.save"
    LABEL_DELETE = "label.delete"
    LABEL_ADD_CONNECTION = "label.add_connection"
    LABEL_BACK = "label.back"
    LABEL_CONTEXT = "label.context"
    LABEL_TEXT_SELECTION = "label.text_selection"
    LABEL_RUN = "label.run"
    LABEL_SETUP = "label.setup"
    LABEL_SETUP_REQUIRED = "label.setup_required"
    LABEL_SELECT_MODEL = "label.select_model"
    LABEL_SELECT_PROVIDER = "label.select_provider"
    LABEL_SELECT_CONNECTION = "label.select_connection"
    LABEL_CONNECTION_ID = "label.connection_id"
    LABEL_MODEL_ID = "label.model_id"
    LABEL_API_KEY = "label.api_key"
    LABEL_UPDATE_CONNECTION = "label.update_connection"
    LABEL_SAVE_CONNECTION = "label.save_connection"
    LABEL_SAVING = "label.saving"
    LABEL_CANCEL_EDIT = "label.cancel_edit"
    LABEL_ADD_NEW = "label.add_new"
    LABEL_EDIT = "label.edit"
    LABEL_DELETE_CONFIRM = "label.delete_confirm"
    LABEL_ENABLE_HISTORY = "label.enable_history"
    LABEL_NO_HISTORY = "label.no_history"
    LABEL_NO_CONNECTIONS = "label.no_connections"
    LABEL_GENERAL = "label.general"
    LABEL_HISTORY = "label.history"
    LABEL_CONNECTIONS = "label.connections"
    LABEL_GLOBAL_SHORTCUTS = "label.global_shortcuts"
    LABEL_MAIN_TRIGGER = "label.main_trigger"
    LABEL_MAIN_TRIGGER_DESC = "label.main_trigger_desc"
    LABEL_ROUTING_DEFAULTS = "label.routing_defaults"
    LABEL_DEFAULT_TEXT_AI = "label.default_text_ai"
    LABEL_ACTIVE_CONNECTIONS = "label.active_connections"
    LABEL_SESSION_HISTORY = "label.session_history"
    LABEL_NEW_HOTKEY = "label.new_hotkey"
    LABEL_CUSTOM_AI_COMMAND = "label.custom_ai_command"
    LABEL_TRIGGER = "label.trigger"
    LABEL_PROMPT = "label.prompt"
    
    # Placeholders
    PLACEHOLDER_PROMPT_INPUT = "placeholder.prompt_input"
    PLACEHOLDER_HOTKEY_TRIGGER = "placeholder.hotkey_trigger"
    
    # Tooltips
    TOOLTIP_RUN_DEFAULT_AI = "tooltip.run_default_ai"
    
    # Built-in Hotkeys
    HK_PASTE_PLAIN = "builtin.paste_plain_unformatted_text"
    HK_PASTE_PLAIN_DESC = "builtin.paste_plain_desc"
    HK_OCR = "builtin.paste_image_to_text_ocr"
    HK_OCR_DESC = "builtin.paste_image_to_text_ocr_desc"
    HK_STT_MIC = "builtin.paste_audio_microphone_to_text"
    HK_STT_MIC_DESC = "builtin.paste_audio_microphone_to_text_desc"
    HK_STT_FILE = "builtin.paste_audio_file_to_text"
    HK_STT_FILE_DESC = "builtin.paste_audio_file_to_text_desc"

class UiTextCatalog:
    """
    Single Source of Truth for all user-visible text.
    Handles fallback logic and language lookup (stubbed for 'en' now).
    """
    
    _DEFAULTS = {
        # App Metadata
        UiTextKey.APP_NAME: "Paste & Speech AI",
        
        # Trust
        UiTextKey.TRUST_NOTICE: "AI can make mistakes. Please review important outputs before you use or share them.",
        
        # Consent
        UiTextKey.CONSENT_AZURE_REQUIRED: "By adding an Azure key, you confirm that you accept Microsoft usage/data processing terms and are comfortable with Microsoft licensing, contract terms, and data protection (Vertragsbedingungen und Microsoft Datenschutzbestimmungen).",
        UiTextKey.CONSENT_OPENAI_REQUIRED: "By adding an OpenAI key, you confirm that you accept OpenAI terms of use and privacy policy (OpenAI Nutzungsbedingungen und Datenschutzrichtlinie).",
        UiTextKey.CONSENT_MISTRAL_REQUIRED: "By adding a Mistral key, you confirm that you accept Mistral terms of use and privacy policy (Mistral Nutzungsbedingungen und Mistral Datenschutzrichtlinie).",
        UiTextKey.CONSENT_GOOGLE_REQUIRED: "By adding a Google key, you confirm that you accept Google terms of use and privacy policy (Google Nutzungsbedingungen und Google Datenschutzrichtlinie).",
        
        # Legal
        UiTextKey.LEGAL_TERMS: "Nutzungsbedingungen",
        UiTextKey.LEGAL_PRIVACY: "Datenschutzrichtlinie",
        UiTextKey.LEGAL_MS_PRIVACY: "Microsoft Datenschutzbestimmungen",
        
        # Errors
        UiTextKey.ERR_CONNECTION_REQUIRED: "This action needs an API provider connection. You can add your API key now; until then this action stays unavailable.",
        UiTextKey.ERR_AUTH_FAILED: "Authentication failed. Please check your API key.",
        UiTextKey.ERR_PROVIDER_UNAVAILABLE: "Provider is currently unavailable.",
        
        # Status
        UiTextKey.STATUS_NOT_READY: "Not ready",
        UiTextKey.STATUS_READY: "Ready",
        UiTextKey.STATUS_DISCONNECTED: "Disconnected",
        
        # General Labels
        UiTextKey.LABEL_HOTKEYS: "Hotkeys",
        UiTextKey.LABEL_SETTINGS: "Settings",
        UiTextKey.LABEL_SAVE: "Save",
        UiTextKey.LABEL_DELETE: "Delete",
        UiTextKey.LABEL_ADD_CONNECTION: "Add Connection",
        UiTextKey.LABEL_BACK: "← Back",
        UiTextKey.LABEL_CONTEXT: "Context",
        UiTextKey.LABEL_TEXT_SELECTION: "Text Selection",
        UiTextKey.LABEL_RUN: "Run",
        UiTextKey.LABEL_SETUP: "Setup",
        UiTextKey.LABEL_SETUP_REQUIRED: "Setup Required",
        UiTextKey.LABEL_SELECT_MODEL: "Select Model",
        UiTextKey.LABEL_SELECT_PROVIDER: "Select Provider",
        UiTextKey.LABEL_SELECT_CONNECTION: "Select a connection...",
        UiTextKey.LABEL_CONNECTION_ID: "Connection ID",
        UiTextKey.LABEL_MODEL_ID: "Model ID",
        UiTextKey.LABEL_API_KEY: "API Key",
        UiTextKey.LABEL_UPDATE_CONNECTION: "Update Connection",
        UiTextKey.LABEL_SAVE_CONNECTION: "Save Connection",
        UiTextKey.LABEL_SAVING: "Saving...",
        UiTextKey.LABEL_CANCEL_EDIT: "Cancel Edit",
        UiTextKey.LABEL_ADD_NEW: "Add New",
        UiTextKey.LABEL_EDIT: "Edit",
        UiTextKey.LABEL_DELETE_CONFIRM: "Delete connection {id}?",
        UiTextKey.LABEL_ENABLE_HISTORY: "Enable History",
        UiTextKey.LABEL_NO_HISTORY: "No history",
        UiTextKey.LABEL_NO_CONNECTIONS: "No connections found.",
        UiTextKey.LABEL_GENERAL: "General",
        UiTextKey.LABEL_HISTORY: "History",
        UiTextKey.LABEL_CONNECTIONS: "Connections",
        UiTextKey.LABEL_GLOBAL_SHORTCUTS: "Global Shortcuts",
        UiTextKey.LABEL_MAIN_TRIGGER: "Main Trigger",
        UiTextKey.LABEL_MAIN_TRIGGER_DESC: "The chord to open the panel",
        UiTextKey.LABEL_ROUTING_DEFAULTS: "Routing Defaults",
        UiTextKey.LABEL_DEFAULT_TEXT_AI: "Default Text AI",
        UiTextKey.LABEL_ACTIVE_CONNECTIONS: "Active Connections",
        UiTextKey.LABEL_SESSION_HISTORY: "Session History",
        UiTextKey.LABEL_NEW_HOTKEY: "New Hotkey",
        UiTextKey.LABEL_CUSTOM_AI_COMMAND: "Custom AI Command",
        UiTextKey.LABEL_TRIGGER: "Trigger",
        UiTextKey.LABEL_PROMPT: "Prompt",
        
        # Placeholders
        UiTextKey.PLACEHOLDER_PROMPT_INPUT: "Enter instructions... (Ctrl+Enter to send)",
        UiTextKey.PLACEHOLDER_HOTKEY_TRIGGER: "e.g. <ctrl>+<alt>+k",
        
        # Tooltips
        UiTextKey.TOOLTIP_RUN_DEFAULT_AI: "Run Default AI Command",
        
        # Built-in Hotkeys
        UiTextKey.HK_PASTE_PLAIN: "Paste as Plain Text",
        UiTextKey.HK_PASTE_PLAIN_DESC: "Strips formatting and pastes unformatted text.",
        UiTextKey.HK_OCR: "Image to Text (OCR)",
        UiTextKey.HK_OCR_DESC: "Extracts text from the latest image on your clipboard.",
        UiTextKey.HK_STT_MIC: "Microphone to Text",
        UiTextKey.HK_STT_MIC_DESC: "Transcribes audio from your microphone.",
        UiTextKey.HK_STT_FILE: "Audio File to Text",
        UiTextKey.HK_STT_FILE_DESC: "Transcribes the latest audio file on your clipboard.",
    }

    @classmethod
    def get(cls, key: UiTextKey, lang: str = "en") -> str:
        # MVP: Support 'en' defaults; future can load from json/po files
        return cls._DEFAULTS.get(key, f"[{key.value}]")

# Global accessor
def get_text(key: UiTextKey) -> str:
    return UiTextCatalog.get(key)
