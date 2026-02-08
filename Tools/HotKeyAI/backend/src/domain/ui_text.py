from typing import Dict, Optional
from pydantic import BaseModel
from enum import Enum

class UiTextKey(str, Enum):
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
    
    # General UI
    STATUS_NOT_READY = "status.not_ready"
    LABEL_HOTKEYS = "label.hotkeys"

class UiTextCatalog:
    """
    Single Source of Truth for all user-visible text.
    Handles fallback logic and language lookup (stubbed for 'en' now).
    """
    
    _DEFAULTS = {
        UiTextKey.TRUST_NOTICE: "AI can make mistakes. Please review important outputs before you use or share them.",
        
        UiTextKey.CONSENT_AZURE_REQUIRED: "By adding an Azure key, you confirm that you accept Microsoft usage/data processing terms and are comfortable with Microsoft licensing, contract terms, and data protection (Vertragsbedingungen und Microsoft Datenschutzbestimmungen).",
        UiTextKey.CONSENT_OPENAI_REQUIRED: "By adding an OpenAI key, you confirm that you accept OpenAI terms of use and privacy policy (OpenAI Nutzungsbedingungen und Datenschutzrichtlinie).",
        UiTextKey.CONSENT_MISTRAL_REQUIRED: "By adding a Mistral key, you confirm that you accept Mistral terms of use and privacy policy (Mistral Nutzungsbedingungen und Mistral Datenschutzrichtlinie).",
        UiTextKey.CONSENT_GOOGLE_REQUIRED: "By adding a Google key, you confirm that you accept Google terms of use and privacy policy (Google Nutzungsbedingungen und Google Datenschutzrichtlinie).",
        
        UiTextKey.LEGAL_TERMS: "Nutzungsbedingungen",
        UiTextKey.LEGAL_PRIVACY: "Datenschutzrichtlinie",
        UiTextKey.LEGAL_MS_PRIVACY: "Microsoft Datenschutzbestimmungen",
        
        UiTextKey.ERR_CONNECTION_REQUIRED: "This action needs an API provider connection. You can add your API key now; until then this action stays unavailable.",
        UiTextKey.STATUS_NOT_READY: "Not ready",
        UiTextKey.LABEL_HOTKEYS: "Hotkeys",
    }

    @classmethod
    def get(cls, key: UiTextKey, lang: str = "en") -> str:
        # MVP: Support 'en' defaults; future can load from json/po files
        return cls._DEFAULTS.get(key, f"[{key.value}]")

# Global accessor
def get_text(key: UiTextKey) -> str:
    return UiTextCatalog.get(key)
