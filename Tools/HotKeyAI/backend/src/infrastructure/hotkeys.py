from pynput import keyboard
from typing import Callable, Optional, Dict
import time
import threading
from loguru import logger

class HotkeyAgent:
    """
    Manages low-level keyboard hooks to detect:
    1. The primary chord: Ctrl+V,V
    2. Global/Direct hotkeys (future)
    """

    def __init__(self, 
                 on_trigger: Callable[[], None], 
                 second_v_timeout_ms: int = 500):
        self.on_trigger = on_trigger
        self.timeout_s = second_v_timeout_ms / 1000.0
        
        self.listener: Optional[keyboard.Listener] = None
        
        # State Machine
        self._ctrl_down = False
        self._first_v_pressed = False
        self._first_v_time = 0.0
        
        # Lock for thread safety during hook callbacks
        self._lock = threading.Lock()

    def start(self):
        logger.info("Starting HotkeyAgent hook...")
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
        logger.info("HotkeyAgent hook stopped.")

    def _reset_chord(self):
        self._first_v_pressed = False
        self._first_v_time = 0.0
        # Do NOT reset Ctrl down state here, as user might still be holding it

    def _on_press(self, key):
        try:
            with self._lock:
                # 1. Check for Ctrl
                if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                    self._ctrl_down = True
                    return

                # 2. Check for V
                if hasattr(key, 'char') and key.char is not None and key.char.lower() == 'v':
                    if self._ctrl_down:
                        now = time.time()
                        
                        if not self._first_v_pressed:
                            # Step 1: First V press
                            self._first_v_pressed = True
                            self._first_v_time = now
                            logger.debug("Chord: First V pressed")
                        else:
                            # Step 2: Second V press?
                            diff = now - self._first_v_time
                            if diff <= self.timeout_s:
                                logger.info(f"Chord: TRIGGERED (delta {diff:.3f}s)")
                                self._reset_chord()
                                # Dispatch trigger in separate thread to not block hook
                                threading.Thread(target=self.on_trigger, daemon=True).start()
                            else:
                                # Timeout exceeded, treat this as a potentially new First V?
                                # Or just reset. For safe "paste-passthrough", we reset.
                                logger.debug("Chord: Timeout exceeded, resetting.")
                                self._first_v_pressed = True # Treat as new start? Or strict reset?
                                self._first_v_time = now
                    else:
                        # V pressed without Ctrl
                        self._reset_chord()
                    return

                # 3. Any other key resets the chord state (except modifiers maybe)
                if key not in [keyboard.Key.shift, keyboard.Key.alt_l, keyboard.Key.alt_r]:
                     self._reset_chord()

        except Exception as e:
            logger.error(f"Error in hook callback: {e}")

    def _on_release(self, key):
        with self._lock:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self._ctrl_down = False
                self._reset_chord()
