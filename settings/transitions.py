from __future__ import annotations

import obspython as obs
from bmd_hid_device.cutmode import CutMode

from settings.manager import SettingsManager


class TransitionSettings(SettingsManager):
    MODE_NONE = "transition_disabled"
    MODE_CUT = "transition_cut"
    MODE_DIS = "transition_dis"
    MODE_SMTH_CUT = "transition_smth_cut"

    _transitions: dict[CutMode, int]
    _skip_transition: int

    def __init__(self):
        self._transitions = {}
        self._skip_transition = -1

    def properties(self, properties: obs.Properties):
        transitions = obs.obs_frontend_get_transitions()
        transition_none = obs.obs_properties_add_list(
            properties, self.MODE_NONE, "Transition: None",
            obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
        transition_cut = obs.obs_properties_add_list(
            properties, self.MODE_CUT, "Transition: Cut",
            obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
        transition_dis = obs.obs_properties_add_list(
            properties, self.MODE_DIS, "Transition: Dis",
            obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
        transition_smth_cut = obs.obs_properties_add_list(
            properties, self.MODE_SMTH_CUT, "Transition: Smth Cut",
            obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
        obs.obs_property_list_add_int(transition_none, "None", -1)
        obs.obs_property_list_add_int(transition_cut, "None", -1)
        obs.obs_property_list_add_int(transition_dis, "None", -1)
        obs.obs_property_list_add_int(transition_smth_cut, "None", -1)
        for index, transition in enumerate(transitions):
            transition_name = obs.obs_source_get_name(transition)
            obs.obs_property_list_add_int(transition_none, transition_name, index)
            obs.obs_property_list_add_int(transition_cut, transition_name, index)
            obs.obs_property_list_add_int(transition_dis, transition_name, index)
            obs.obs_property_list_add_int(transition_smth_cut, transition_name, index)
        obs.source_list_release(transitions)

    def defaults(self, settings: obs.Data):
        transitions = obs.obs_frontend_get_transitions()
        transition_ids = [obs.obs_source_get_id(transition) for transition in transitions]
        obs.source_list_release(transitions)
        obs.obs_data_set_autoselect_int(settings, self.MODE_NONE, -1)
        obs.obs_data_set_autoselect_int(settings, self.MODE_CUT, -1)
        obs.obs_data_set_autoselect_int(settings, self.MODE_DIS, -1)
        obs.obs_data_set_autoselect_int(settings, self.MODE_SMTH_CUT, -1)
        cut_idx = transition_ids.index("cut_transition")
        obs.obs_data_set_default_int(settings, self.MODE_NONE, cut_idx)
        obs.obs_data_set_default_int(settings, self.MODE_CUT, cut_idx)
        fade_idx = transition_ids.index("fade_transition")
        obs.obs_data_set_default_int(settings, self.MODE_DIS, fade_idx)
        obs.obs_data_set_default_int(settings, self.MODE_SMTH_CUT, -1)

    def update(self, settings: obs.Data):
        self._skip_transition = obs.obs_data_get_int(settings, self.MODE_NONE)
        self._transitions = {
            CutMode.CUT: obs.obs_data_get_int(settings, self.MODE_CUT),
            CutMode.DIS: obs.obs_data_get_int(settings, self.MODE_DIS),
            CutMode.SMTH_CUT: obs.obs_data_get_int(settings, self.MODE_SMTH_CUT),
        }

    def get_modes(self, index: int) -> (set[CutMode], bool):
        modes = set(mode for mode in CutMode if self._transitions[mode] == index)
        skip_transitions = self._skip_transition == index
        return modes, skip_transitions

    def get_transition(self, modes: list[CutMode]) -> (list[int], int):
        return [self._transitions[mode] for mode in modes], self._skip_transition
