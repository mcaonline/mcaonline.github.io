import pyperclip
import time
from typing import Optional
from pynput import keyboard
from loguru import logger
from PIL import Image, ImageGrab
from io import BytesIO

class ClipboardManager:
    """
    Unified interface for Clipboard and Selected Text capture.
    """

    def read_text(self) -> str:
        return pyperclip.paste()

    def write_text(self, text: str):
        pyperclip.copy(text)

    def read_image(self) -> Optional[Image.Image]:
        """Reads an image from the clipboard if present."""
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                return img
            return None
        except Exception as e:
            logger.error(f"Failed to read image from clipboard: {e}")
            return None

    def get_selected_text(self) -> Optional[str]:
        """
        Captures selected text by simulating Ctrl+C.
        Preserves original clipboard content if possible.
        """
        # 1. Snapshot current clipboard
        original_content = self.read_text()
        
        # 2. Clear clipboard to detect if copy worked
        self.write_text("")
        
        # 3. Simulate Ctrl+C
        self._simulate_ctrl_c()
        
        # 4. Wait for OS to process
        max_retries = 10
        captured_text = ""
        for _ in range(max_retries):
            captured_text = self.read_text()
            if captured_text:
                break
            time.sleep(0.05)
            
        if not captured_text:
            self.write_text(original_content)
            return None
            
        return captured_text

    def _simulate_ctrl_c(self):
        """Sends synthetic Ctrl+C."""
        try:
            c = keyboard.Controller()
            with c.pressed(keyboard.Key.ctrl):
                c.press('c')
                c.release('c')
            logger.debug("Simulated Ctrl+C for selection capture")
        except Exception as e:
            logger.error(f"Failed to simulate Ctrl+C: {e}")

# Global instance
clipboard = ClipboardManager()
