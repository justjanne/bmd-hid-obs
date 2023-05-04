from __future__ import annotations

import math
import time
from typing import Optional

import obspython as obs
from bmd_hid_device.cutmode import CutMode
from bmd_hid_device.devices import BmdDeviceId
from bmd_hid_device.hiddevice import BmdHidDevice
from bmd_hid_device.jogmode import JogMode
from bmd_hid_device.protocol.types import BmdHidLed, BmdHidKey, BmdHidJogMode

import frontend_events

cam_leds = [BmdHidLed.CAM1, BmdHidLed.CAM2, BmdHidLed.CAM3,
            BmdHidLed.CAM4, BmdHidLed.CAM5, BmdHidLed.CAM6,
            BmdHidLed.CAM7, BmdHidLed.CAM8, BmdHidLed.CAM9]
cam_keys = [BmdHidKey.CAM1, BmdHidKey.CAM2, BmdHidKey.CAM3,
            BmdHidKey.CAM4, BmdHidKey.CAM5, BmdHidKey.CAM6,
            BmdHidKey.CAM7, BmdHidKey.CAM8, BmdHidKey.CAM9]
all_cam_leds = BmdHidLed.CAM1 | BmdHidLed.CAM2 | BmdHidLed.CAM3 | \
               BmdHidLed.CAM4 | BmdHidLed.CAM5 | BmdHidLed.CAM6 | \
               BmdHidLed.CAM7 | BmdHidLed.CAM8 | BmdHidLed.CAM9

FRONTEND_EVENT_NAMES: dict[obs.FrontendEvent, str] = {
    obs.OBS_FRONTEND_EVENT_STREAMING_STARTING: "OBS_FRONTEND_EVENT_STREAMING_STARTING",
    obs.OBS_FRONTEND_EVENT_STREAMING_STARTED: "OBS_FRONTEND_EVENT_STREAMING_STARTED",
    obs.OBS_FRONTEND_EVENT_STREAMING_STOPPING: "OBS_FRONTEND_EVENT_STREAMING_STOPPING",
    obs.OBS_FRONTEND_EVENT_STREAMING_STOPPED: "OBS_FRONTEND_EVENT_STREAMING_STOPPED",
    obs.OBS_FRONTEND_EVENT_RECORDING_STARTING: "OBS_FRONTEND_EVENT_RECORDING_STARTING",
    obs.OBS_FRONTEND_EVENT_RECORDING_STARTED: "OBS_FRONTEND_EVENT_RECORDING_STARTED",
    obs.OBS_FRONTEND_EVENT_RECORDING_STOPPING: "OBS_FRONTEND_EVENT_RECORDING_STOPPING",
    obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED: "OBS_FRONTEND_EVENT_RECORDING_STOPPED",
    obs.OBS_FRONTEND_EVENT_SCENE_CHANGED: "OBS_FRONTEND_EVENT_SCENE_CHANGED",
    obs.OBS_FRONTEND_EVENT_SCENE_LIST_CHANGED: "OBS_FRONTEND_EVENT_SCENE_LIST_CHANGED",
    obs.OBS_FRONTEND_EVENT_TRANSITION_CHANGED: "OBS_FRONTEND_EVENT_TRANSITION_CHANGED",
    obs.OBS_FRONTEND_EVENT_TRANSITION_STOPPED: "OBS_FRONTEND_EVENT_TRANSITION_STOPPED",
    obs.OBS_FRONTEND_EVENT_TRANSITION_LIST_CHANGED: "OBS_FRONTEND_EVENT_TRANSITION_LIST_CHANGED",
    obs.OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGED: "OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGED",
    obs.OBS_FRONTEND_EVENT_SCENE_COLLECTION_LIST_CHANGED: "OBS_FRONTEND_EVENT_SCENE_COLLECTION_LIST_CHANGED",
    obs.OBS_FRONTEND_EVENT_PROFILE_CHANGED: "OBS_FRONTEND_EVENT_PROFILE_CHANGED",
    obs.OBS_FRONTEND_EVENT_PROFILE_LIST_CHANGED: "OBS_FRONTEND_EVENT_PROFILE_LIST_CHANGED",
    obs.OBS_FRONTEND_EVENT_EXIT: "OBS_FRONTEND_EVENT_EXIT",

    obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTING: "OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTING",
    obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED: "OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED",
    obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPING: "OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPING",
    obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPED: "OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPED",

    obs.OBS_FRONTEND_EVENT_STUDIO_MODE_ENABLED: "OBS_FRONTEND_EVENT_STUDIO_MODE_ENABLED",
    obs.OBS_FRONTEND_EVENT_STUDIO_MODE_DISABLED: "OBS_FRONTEND_EVENT_STUDIO_MODE_DISABLED",
    obs.OBS_FRONTEND_EVENT_PREVIEW_SCENE_CHANGED: "OBS_FRONTEND_EVENT_PREVIEW_SCENE_CHANGED",

    obs.OBS_FRONTEND_EVENT_SCENE_COLLECTION_CLEANUP: "OBS_FRONTEND_EVENT_SCENE_COLLECTION_CLEANUP",
    obs.OBS_FRONTEND_EVENT_FINISHED_LOADING: "OBS_FRONTEND_EVENT_FINISHED_LOADING",

    obs.OBS_FRONTEND_EVENT_RECORDING_PAUSED: "OBS_FRONTEND_EVENT_RECORDING_PAUSED",
    obs.OBS_FRONTEND_EVENT_RECORDING_UNPAUSED: "OBS_FRONTEND_EVENT_RECORDING_UNPAUSED",

    obs.OBS_FRONTEND_EVENT_TRANSITION_DURATION_CHANGED: "OBS_FRONTEND_EVENT_TRANSITION_DURATION_CHANGED",
    obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED: "OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED",

    obs.OBS_FRONTEND_EVENT_VIRTUALCAM_STARTED: "OBS_FRONTEND_EVENT_VIRTUALCAM_STARTED",
    obs.OBS_FRONTEND_EVENT_VIRTUALCAM_STOPPED: "OBS_FRONTEND_EVENT_VIRTUALCAM_STOPPED",

    obs.OBS_FRONTEND_EVENT_TBAR_VALUE_CHANGED: "OBS_FRONTEND_EVENT_TBAR_VALUE_CHANGED",
    obs.OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGING: "OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGING",
    obs.OBS_FRONTEND_EVENT_PROFILE_CHANGING: "OBS_FRONTEND_EVENT_PROFILE_CHANGING",
    obs.OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN: "OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN",
    obs.OBS_FRONTEND_EVENT_PROFILE_RENAMED: "OBS_FRONTEND_EVENT_PROFILE_RENAMED",
    obs.OBS_FRONTEND_EVENT_SCENE_COLLECTION_RENAMED: "OBS_FRONTEND_EVENT_SCENE_COLLECTION_RENAMED",
    obs.OBS_FRONTEND_EVENT_THEME_CHANGED: "OBS_FRONTEND_EVENT_THEME_CHANGED",
    obs.OBS_FRONTEND_EVENT_SCREENSHOT_TAKEN: "OBS_FRONTEND_EVENT_SCREENSHOT_TAKEN",
}


def get_current_cut_mode() -> CutMode:
    current_transition = obs.obs_frontend_get_current_transition()
    current_transition_name = None
    if current_transition is not None:
        current_transition_name = obs.obs_source_get_name(current_transition)
    obs.obs_source_release(current_transition)
    if current_transition_name == "Cut":
        return CutMode.CUT
    elif current_transition_name == "Fade":
        return CutMode.DIS
    else:
        return CutMode.SMTH_CUT


def source_str(source: obs.Source):
    return "Source(id={0},type={1},name={2})".format(
        obs.obs_source_get_id(source),
        obs.obs_source_get_type(source),
        obs.obs_source_get_name(source)
    )


class ObsBmdDevice(BmdHidDevice):
    cut_mode: CutMode
    jog_mode: JogMode
    use_transitions: bool
    live_overwrite: bool
    duration: Optional[int]
    last_duration_set: Optional[int]

    def __init__(self, device: BmdDeviceId):
        super().__init__(device)
        frontend_events.add_frontend_event_listener(self.on_frontend_event)
        obs.script_log(obs.LOG_INFO, "{0} registered for frontend events".format(self))
        self.leds.clear()
        self.update_jog_mode(JogMode.SCRL)
        self.on_cut_mode_changed()
        self.use_transitions = True
        self.update_transition_state()
        self.live_overwrite = False
        self.duration = None
        self.last_duration_set = None

    def close(self):
        frontend_events.remove_frontend_event_listener(self.on_frontend_event)
        obs.script_log(obs.LOG_INFO, "{0} unregistered for frontend events".format(self))
        super().close()

    def update_jog_mode(self, mode: JogMode):
        self.jog_mode = mode
        with self.leds as leds:
            leds.off(JogMode.leds())
            leds.on(mode.led())
        self.set_jog_mode(mode.mode())

    def update_cut_mode(self, mode: CutMode):
        self.cut_mode = mode
        if mode == CutMode.CUT:
            transition = obs.obs_get_transition_by_name("Cut")
        elif mode == CutMode.DIS:
            transition = obs.obs_get_transition_by_name("Fade")
        else:
            transition = None
        if transition is not None:
            obs.obs_frontend_set_current_transition(transition)
            obs.obs_source_release(transition)

    def on_cut_mode_changed(self):
        cut_mode = get_current_cut_mode()
        obs.script_log(obs.LOG_DEBUG, "cut mode changed, current cut mode: {0}".format(
            cut_mode.name
        ))
        with self.leds as leds:
            leds.off(CutMode.leds())
            leds.on(cut_mode.led())

    def get_current_cam(self) -> Optional[int]:
        scenes = obs.obs_frontend_get_scenes()
        scene_names = [obs.obs_source_get_name(scene) for scene in scenes]
        obs.source_list_release(scenes)
        if self.live_overwrite:
            preview_scene = obs.obs_frontend_get_current_preview_scene()
            preview_scene_name = obs.obs_source_get_name(preview_scene)
            obs.obs_source_release(preview_scene)
            index = scene_names.index(preview_scene_name)
        else:
            preview_scene = obs.obs_frontend_get_current_scene()
            preview_scene_name = obs.obs_source_get_name(preview_scene)
            obs.obs_source_release(preview_scene)
            index = scene_names.index(preview_scene_name)
        if index < 0 or index > len(cam_leds):
            return None
        return index

    def on_scene_changed(self):
        index = self.get_current_cam()
        obs.script_log(obs.LOG_DEBUG, "scene changed, current scene: {0}".format(
            index + 1
        ))
        with self.leds as leds:
            leds.off(all_cam_leds)
            if index is not None:
                leds.on(cam_leds[index])

    def switch_scene(self, id: int):
        scenes = obs.obs_frontend_get_scenes()
        if len(scenes) > id:
            obs.script_log(obs.LOG_DEBUG, "Switching to scene {0} {1}".format(
                id,
                source_str(scenes[id])
            ))
            obs.obs_frontend_set_current_preview_scene(scenes[id])
            obs.source_list_release(scenes)
            if self.live_overwrite:
                self.trigger_transition()

    def on_frontend_event(self, event: obs.FrontendEvent):
        if self.isclosed():
            return
        if event == obs.OBS_FRONTEND_EVENT_TRANSITION_CHANGED:
            self.on_cut_mode_changed()
        elif event == obs.OBS_FRONTEND_EVENT_PREVIEW_SCENE_CHANGED:
            self.on_scene_changed()
        elif event == obs.OBS_FRONTEND_EVENT_TRANSITION_DURATION_CHANGED:
            pass
        else:
            obs.script_log(obs.LOG_DEBUG, "on_frontend_event: {0}".format(FRONTEND_EVENT_NAMES[event]))

    def _map_jog_value(self, value: int, pivot: float, curve: float) -> float:
        sign = math.copysign(1, value)
        abs = math.fabs(value / 360)
        mapped_value = pivot * math.pow(abs / pivot, curve)
        return sign * mapped_value

    def on_jog_event(self, mode: BmdHidJogMode, value: int):
        if BmdHidKey.TRANS_DUR in self.held_keys and self.duration is not None:
            self.duration += self._map_jog_value(value, 200, 2.2)
            if self.duration < 50:
                self.duration = 50
            if self.duration > 20000:
                self.duration = 20000
            now = time.monotonic_ns()
            if self.last_duration_set is None or now - self.last_duration_set > 1_000_000:
                obs.obs_frontend_set_transition_duration(int(self.duration))
                self.last_duration_set = now
                obs.script_log(obs.LOG_DEBUG, "trans_dur {0}".format(self.duration))

    def update_transition_state(self):
        with self.leds as leds:
            leds.off(BmdHidLed.TRANS)
            if self.use_transitions:
                self.leds.on(BmdHidLed.TRANS)

    def trigger_transition(self):
        duration = obs.obs_frontend_get_transition_duration()
        if not self.use_transitions:
            obs.obs_frontend_set_transition_duration(0)
            obs.obs_frontend_preview_program_trigger_transition()
            obs.obs_frontend_set_transition_duration(duration)
        else:
            obs.obs_frontend_preview_program_trigger_transition()

    def on_key_down(self, key: BmdHidKey):
        obs.script_log(obs.LOG_DEBUG, "on_key_down: {0}".format(key.name))
        if key == BmdHidKey.SHTL:
            self.update_jog_mode(JogMode.SHTL)
        elif key == BmdHidKey.JOG:
            self.update_jog_mode(JogMode.JOG)
        elif key == BmdHidKey.SCRL:
            self.update_jog_mode(JogMode.SCRL)
        elif key == BmdHidKey.CUT:
            self.update_cut_mode(CutMode.CUT)
        elif key == BmdHidKey.DIS:
            self.update_cut_mode(CutMode.DIS)
        elif key == BmdHidKey.SMTH_CUT:
            self.update_cut_mode(CutMode.SMTH_CUT)
        elif key == BmdHidKey.TRANS:
            self.use_transitions = not self.use_transitions
            self.update_transition_state()
        elif key == BmdHidKey.TRANS_DUR:
            self.duration = obs.obs_frontend_get_transition_duration()
            self.set_jog_mode(BmdHidJogMode.RELATIVE_DEADZONE)
        elif key in cam_keys:
            self.switch_scene(cam_keys.index(key))
        elif key == BmdHidKey.LIVE_OWR:
            self.live_overwrite = not self.live_overwrite
            with self.leds as leds:
                leds.off(BmdHidLed.LIVE_OWR)
                if self.live_overwrite:
                    leds.on(BmdHidLed.LIVE_OWR)
        elif key == BmdHidKey.STOP_PLAY:
            self.trigger_transition()

    def on_key_up(self, key: BmdHidKey):
        if key == BmdHidKey.TRANS_DUR:
            self.set_jog_mode(self.jog_mode.mode())
            self.duration = None

    def on_battery(self, charging: bool, level: int):
        pass
