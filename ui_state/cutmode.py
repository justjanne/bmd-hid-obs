from __future__ import annotations

import obspython as obs
from bmd_hid_device.cutmode import CutMode
from bmd_hid_device.protocol.types import BmdHidLed

from settings.transitions import TransitionSettings


def _current_transition_index() -> int:
    transitions = obs.obs_frontend_get_transitions()
    current_transition = obs.obs_frontend_get_current_transition()
    transition_names = [obs.obs_source_get_name(transition) for transition in transitions]
    current_transition_name = obs.obs_source_get_name(current_transition) if current_transition is not None else None
    obs.source_list_release(transitions)
    obs.obs_source_release(current_transition)
    return transition_names.index(current_transition_name)


def _set_transition_from_index(index: int):
    transitions = obs.obs_frontend_get_transitions()
    try:
        if 0 <= index < len(transitions):
            obs.obs_frontend_set_current_transition(transitions[index])
            return True
    finally:
        obs.source_list_release(transitions)
    return False


class CutModeHandler:
    transition_settings: TransitionSettings
    active_modes: list[CutMode]
    skip_transitions: bool

    def __init__(self, settings: TransitionSettings):
        self.transition_settings = settings
        self.skip_transitions = False
        self.active_modes = []

    @staticmethod
    def all_leds() -> BmdHidLed:
        return CutMode.leds() | BmdHidLed.TRANS

    def _determine_leds(self) -> BmdHidLed:
        if self.skip_transitions:
            return BmdHidLed(0)
        else:
            result = BmdHidLed.TRANS
            for mode in self.active_modes:
                result |= mode.led()
            return result

    def _apply_mode(self):
        indices, skip_transition = self.transition_settings.get_transition(self.active_modes)
        if self.skip_transitions:
            _set_transition_from_index(skip_transition)
        else:
            for index in indices:
                if _set_transition_from_index(index):
                    break

    def determine_status(self) -> BmdHidLed:
        active_modes, skip_transitions = self.transition_settings.get_modes(_current_transition_index())
        self.skip_transitions &= skip_transitions
        if not self.skip_transitions:
            self.active_modes = active_modes
        return self._determine_leds()

    def set_mode(self, mode: CutMode) -> BmdHidLed:
        if not self.skip_transitions:
            self.active_modes = [mode]
            self._apply_mode()
        return self._determine_leds()

    def toggle_skip_transitions(self) -> BmdHidLed:
        self.skip_transitions = not self.skip_transitions
        self._apply_mode()
        return self._determine_leds()
