import pyperclip
import time
from typing import Optional
from pynput import keyboard
from loguru import logger

class ClipboardManager:
    """
    Unified interface for Clipboard and Selected Text capture.
    """

    def read_text(self) -> str:
        return pyperclip.paste()

    def write_text(self, text: str):
        pyperclip.copy(text)

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
        # Retry loop for a few ms
        max_retries = 10
        captured_text = ""
        for _ in range(max_retries):
            captured_text = self.read_text()
            if captured_text:
                break
            time.sleep(0.05) # 50ms wait
            
        # 5. Restore original if nothing was captured (meaning no selection)
        # OR if we want to be polite. But if we captured something, we usually
        # want to use it.
        # Design decision: If we return a value, we leave it in clipboard?
        # AppDesign says: "If selected text exists... Selected text becomes active source."
        # Usually users expect Ctrl+C to overwrite clipboard.
        
        if not captured_text:
            # Restore original
            self.write_text(original_content)
            return None
            
        return captured_text

    def _simulate_ctrl_c(self):
        """
        Sends synthetic Ctrl+C.
        """
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
