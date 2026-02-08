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
        except Exception as e:
            logger.error(f"Failed to load hotkey catalog: {e}")
            # Backup corrupt file?
            self._seed_defaults()

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
        paste_plain = HotkeyDefinition(
            kind='builtin',
            mode='local_transform',
            display_key='builtin.paste_plain_unformatted_text', # TODO: Add to UiTextCatalog
            description_key='builtin.paste_plain_desc',
            enabled=True,
            sequence=0,
            local_transform_config={
                'type': 'regex',
                'pattern': '.*', # Dummy, logic handled in code for special builtins?
                'replacement': '$0'
            }
        )
        self._catalog.hotkeys.append(paste_plain)
