from typing import List, Optional
from pathlib import Path
import json
from src.domain.models import HotkeyCatalog as HotkeyCatalogModel, HotkeyDefinition, HotkeyKind
from loguru import logger

class HotkeyCatalogService:
    """
    Manages the persistence and retrieval of HotkeyDefinitions.
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self._catalog: HotkeyCatalogModel = HotkeyCatalogModel()
        self.load()

    def load(self):
        if not self.storage_path.exists():
            logger.info("No hotkey catalog found, initializing defaults.")
            self._seed_defaults()
            self.save()
            return
            
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._catalog = HotkeyCatalogModel.model_validate(data)
            
            # Cleanup legacy/duplicates
            self._cleanup_legacy()
            
            # Ensure required built-ins exist
            self._ensure_builtins()
        except Exception as e:
            logger.error(f"Failed to load hotkey catalog: {e}")
            self._seed_defaults()

    def _cleanup_legacy(self):
        """Removes legacy or duplicate hotkeys."""
        # 1. Remove duplicate Paste Plain with UUIDs (keep only 'paste_plain')
        original_count = len(self._catalog.hotkeys)
        self._catalog.hotkeys = [
            h for h in self._catalog.hotkeys 
            if not (h.display_key == 'builtin.paste_plain_unformatted_text' and h.id != 'paste_plain')
        ]
        
        # 2. Deduplicate by ID (keep first)
        seen_ids = set()
        unique_hotkeys = []
        for h in self._catalog.hotkeys:
            if h.id not in seen_ids:
                unique_hotkeys.append(h)
                seen_ids.add(h.id)
        self._catalog.hotkeys = unique_hotkeys
        
        if len(self._catalog.hotkeys) != original_count:
            logger.info("Cleaned up legacy/duplicate hotkeys")
            self.save()

    def _ensure_builtins(self):
        """Ensures all required built-in hotkeys from seed are present."""
        existing_ids = {h.id for h in self._catalog.hotkeys}
        
        # We temporarily seed into a dummy catalog to see what we're missing
        temp_catalog = HotkeyCatalogModel()
        orig_catalog_ref = self._catalog
        self._catalog = temp_catalog
        self._seed_defaults()
        self._catalog = orig_catalog_ref
        
        added = False
        for builtin in temp_catalog.hotkeys:
            if builtin.id not in existing_ids:
                logger.info(f"Restoring missing builtin hotkey: {builtin.id}")
                self._catalog.hotkeys.append(builtin)
                added = True
        
        if added:
            self.save()

    def save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                f.write(self._catalog.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Failed to save hotkey catalog: {e}")

    def get_all(self) -> List[HotkeyDefinition]:
        return self._catalog.hotkeys

    def get(self, hotkey_id: str) -> Optional[HotkeyDefinition]:
        return next((h for h in self._catalog.hotkeys if h.id == hotkey_id), None)

    def add(self, definition: HotkeyDefinition):
        self._catalog.hotkeys.append(definition)
        self.save()
        
    def update(self, definition: HotkeyDefinition):
        for i, h in enumerate(self._catalog.hotkeys):
            if h.id == definition.id:
                self._catalog.hotkeys[i] = definition
                self.save()
                return
        logger.warning(f"Attempted to update non-existent hotkey {definition.id}")

    def delete(self, hotkey_id: str):
        self._catalog.hotkeys = [h for h in self._catalog.hotkeys if h.id != hotkey_id]
        self.save()

    def _seed_defaults(self):
        """
        Seeds required built-in hotkeys per AppDesign.md Contract A1.
        """
        # 1. Paste as Plain Text
        self._catalog.hotkeys.append(HotkeyDefinition(
            id='paste_plain',
            kind='builtin',
            mode='local_transform',
            display_key='builtin.paste_plain_unformatted_text',
            description_key='builtin.paste_plain_desc',
            enabled=True,
            sequence=0,
            local_transform_config={'type': 'regex', 'pattern': '.*', 'replacement': '$0'}
        ))

        # 2. Paste Image to Text (OCR)
        self._catalog.hotkeys.append(HotkeyDefinition(
            id='ocr_paste',
            kind='builtin',
            mode='ai_transform',
            display_key='builtin.paste_image_to_text_ocr',
            description_key='builtin.paste_image_to_text_ocr_desc',
            enabled=False,
            sequence=1,
            capability_requirements=[{'capability': 'ocr', 'min_sequence': 1}]
        ))

        # 3. Paste Audio to Text (STT)
        self._catalog.hotkeys.append(HotkeyDefinition(
            id='stt_paste',
            kind='builtin',
            mode='ai_transform',
            display_key='builtin.paste_audio_microphone_to_text',
            description_key='builtin.paste_audio_microphone_to_text_desc',
            enabled=False,
            sequence=2,
            capability_requirements=[{'capability': 'stt', 'min_sequence': 1}]
        ))
