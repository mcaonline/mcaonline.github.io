from typing import List, Optional
from pathlib import Path
import json
from ..domain.models import ActionCatalog as ActionCatalogModel, ActionDefinition, ActionKind
from ..domain.types import ActionId
from loguru import logger

class ActionCatalogService:
    """
    Manages the persistence and retrieval of ActionDefinitions.
    """

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self._catalog: ActionCatalogModel = ActionCatalogModel()
        self.load()

    def load(self):
        if not self.storage_path.exists():
            logger.info("No action catalog found, initializing defaults.")
            self._seed_defaults()
            self.save()
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Migration: rename "hotkeys" key to "actions" if present
            if "hotkeys" in data and "actions" not in data:
                data["actions"] = data.pop("hotkeys")

            self._catalog = ActionCatalogModel.model_validate(data)

            # Cleanup legacy/duplicates
            self._cleanup_legacy()

            # Ensure required built-ins exist
            self._ensure_builtins()
        except Exception as e:
            logger.error(f"Failed to load action catalog: {e}")
            self._seed_defaults()

    def _cleanup_legacy(self):
        """Removes legacy or duplicate actions."""
        # 1. Remove duplicate Paste Plain with UUIDs (keep only 'paste_plain')
        original_count = len(self._catalog.actions)
        self._catalog.actions = [
            h for h in self._catalog.actions
            if not (h.display_key == 'builtin.paste_plain_unformatted_text' and h.id != 'paste_plain')
        ]

        # 2. Deduplicate by ID (keep first)
        seen_ids = set()
        unique_actions = []
        for h in self._catalog.actions:
            if h.id not in seen_ids:
                unique_actions.append(h)
                seen_ids.add(h.id)
        self._catalog.actions = unique_actions

        if len(self._catalog.actions) != original_count:
            logger.info("Cleaned up legacy/duplicate actions")
            self.save()

    def _ensure_builtins(self):
        """Ensures all required built-in actions from seed are present."""
        existing_ids = {h.id for h in self._catalog.actions}

        # We temporarily seed into a dummy catalog to see what we're missing
        temp_catalog = ActionCatalogModel()
        orig_catalog_ref = self._catalog
        self._catalog = temp_catalog
        self._seed_defaults()
        self._catalog = orig_catalog_ref

        added = False
        for builtin in temp_catalog.actions:
            if builtin.id not in existing_ids:
                logger.info(f"Restoring missing builtin action: {builtin.id}")
                self._catalog.actions.append(builtin)
                added = True

        if added:
            self.save()

    def save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                f.write(self._catalog.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Failed to save action catalog: {e}")

    def get_all(self) -> List[ActionDefinition]:
        return self._catalog.actions

    def get(self, action_id: ActionId) -> Optional[ActionDefinition]:
        return next((h for h in self._catalog.actions if h.id == action_id), None)

    def add(self, definition: ActionDefinition):
        self._catalog.actions.append(definition)
        self.save()

    def update(self, definition: ActionDefinition):
        for i, h in enumerate(self._catalog.actions):
            if h.id == definition.id:
                self._catalog.actions[i] = definition
                self.save()
                return
        logger.warning(f"Attempted to update non-existent action {definition.id}")

    def delete(self, action_id: ActionId):
        self._catalog.actions = [h for h in self._catalog.actions if h.id != action_id]
        self.save()

    def _seed_defaults(self):
        """
        Seeds required built-in actions per AppDesign.md Contract A1.
        """
        # 1. Paste as Plain Text
        self._catalog.actions.append(ActionDefinition(
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
        self._catalog.actions.append(ActionDefinition(
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
        self._catalog.actions.append(ActionDefinition(
            id='stt_paste',
            kind='builtin',
            mode='ai_transform',
            display_key='builtin.paste_audio_microphone_to_text',
            description_key='builtin.paste_audio_microphone_to_text_desc',
            enabled=False,
            sequence=2,
            capability_requirements=[{'capability': 'stt', 'min_sequence': 1}]
        ))
