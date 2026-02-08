from pynput import keyboard
from typing import Callable, Optional, Dict, List
import time
import threading
import os
from loguru import logger
from ..domain.models import ActionDefinition

class ActionAgent:
    """
    Manages low-level keyboard hooks to detect:
    1. The primary chord: Ctrl+V,V (or configured trigger)
    2. Global/Direct hotkeys
    """

    def __init__(self,
                 on_trigger: Callable[[str], None],
                 second_v_timeout_ms: int = 500):
        self.on_trigger = on_trigger # Callback now takes an action_id (or None for panel)
        self.timeout_s = second_v_timeout_ms / 1000.0

        self.listener: Optional[keyboard.Listener] = None
        self.global_hotkeys: Optional[keyboard.GlobalHotKeys] = None

        # State Machine for Chord
        self._ctrl_down = False
        self._first_v_pressed = False
        self._first_v_time = 0.0

        # Lock for thread safety during hook callbacks
        self._lock = threading.Lock()

        self._registered_definitions: List[ActionDefinition] = []

    def start(self):
        pid = os.getpid()
        logger.info(f"[{pid}] Starting ActionAgent hook...")

        # 1. Start low-level listener for Chord logic
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

        # 2. Apply any pending global hotkeys
        self._apply_global_hotkeys()

    def stop(self):
        pid = os.getpid()
        if self.listener:
            self.listener.stop()
            self.listener = None

        if self.global_hotkeys:
            self.global_hotkeys.stop()
            self.global_hotkeys = None

        logger.info(f"[{pid}] ActionAgent hook stopped.")

    def update_actions(self, actions: List[ActionDefinition]):
        """Updates the list of active direct hotkeys."""
        self._registered_definitions = actions
        self._apply_global_hotkeys()

    def _apply_global_hotkeys(self):
        """Re-registers global hotkeys based on current definitions."""
        if self.global_hotkeys:
            self.global_hotkeys.stop()
            self.global_hotkeys = None

        mapping = {}
        for action in self._registered_definitions:
            if action.enabled and action.direct_hotkey:
                try:
                    # Capture action.id in closure
                    trigger_fn = lambda id=action.id: self._dispatch_trigger(id)
                    mapping[action.direct_hotkey] = trigger_fn
                    logger.debug(f"Registered global hotkey: {action.direct_hotkey} -> {action.id}")
                except Exception as e:
                    logger.error(f"Failed to register hotkey {action.direct_hotkey}: {e}")

        if mapping:
            self.global_hotkeys = keyboard.GlobalHotKeys(mapping)
            self.global_hotkeys.start()

    def _dispatch_trigger(self, action_id: Optional[str]):
        threading.Thread(target=self.on_trigger, args=(action_id,), daemon=True).start()

    def _reset_chord(self):
        self._first_v_pressed = False
        self._first_v_time = 0.0

    def _on_press(self, key):
        try:
            with self._lock:
                # 1. Check for Ctrl
                if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                    self._ctrl_down = True
                    return

                # 2. Check for V (Hardcoded Chord for now, Todo: Make configurable)
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
                                self._dispatch_trigger(None) # None = Panel Trigger
                            else:
                                logger.debug("Chord: Timeout exceeded, resetting.")
                                self._first_v_pressed = True
                                self._first_v_time = now
                    else:
                        self._reset_chord()
                    return

                if key not in [keyboard.Key.shift, keyboard.Key.alt_l, keyboard.Key.alt_r]:
                     self._reset_chord()

        except Exception as e:
            logger.error(f"Error in hook callback: {e}")

    def _on_release(self, key):
        with self._lock:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self._ctrl_down = False
                self._reset_chord()
