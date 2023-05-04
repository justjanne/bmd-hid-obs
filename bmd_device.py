from __future__ import annotations

import math
import time
from typing import Optional, Callable

import hid
import obspython as obs
from bmd_hid_device.cutmode import CutMode
from bmd_hid_device.hiddevice import BmdHidDevice
from bmd_hid_device.jogmode import JogMode
from bmd_hid_device.protocol.types import BmdHidLed, BmdHidKey, BmdHidJogMode
from bmd_hid_device.util.deviceinfo import HidDeviceInfo

from events import frontend_event
from settings.transitions import TransitionSettings
from ui_state.cutmode import CutModeHandler
from util import FRONTEND_EVENT_NAMES

cam_leds = [BmdHidLed.CAM1, BmdHidLed.CAM2, BmdHidLed.CAM3,
            BmdHidLed.CAM4, BmdHidLed.CAM5, BmdHidLed.CAM6,
            BmdHidLed.CAM7, BmdHidLed.CAM8, BmdHidLed.CAM9]
cam_keys = [BmdHidKey.CAM1, BmdHidKey.CAM2, BmdHidKey.CAM3,
            BmdHidKey.CAM4, BmdHidKey.CAM5, BmdHidKey.CAM6,
            BmdHidKey.CAM7, BmdHidKey.CAM8, BmdHidKey.CAM9]
all_cam_leds = BmdHidLed.CAM1 | BmdHidLed.CAM2 | BmdHidLed.CAM3 | \
               BmdHidLed.CAM4 | BmdHidLed.CAM5 | BmdHidLed.CAM6 | \
               BmdHidLed.CAM7 | BmdHidLed.CAM8 | BmdHidLed.CAM9


def source_str(source: obs.Source):
    return "Source(id={0},type={1},name={2})".format(
        obs.obs_source_get_id(source),
        obs.obs_source_get_type(source),
        obs.obs_source_get_name(source)
    )


class ObsBmdDevice(BmdHidDevice):
    jog_mode: JogMode
    live_overwrite: bool
    duration: Optional[int]
    last_duration_set: Optional[int]
    transitions: TransitionSettings
    cutmode_handler: CutModeHandler
    on_close: Callable[[], None]

    def __init__(self, device_info: HidDeviceInfo, transitions: TransitionSettings,
                 on_close: Callable[[ObsBmdDevice], None]):
        self.on_close = on_close
        super().__init__(device_info)
        self.transitions = transitions
        frontend_event.add_frontend_event_listener(self.on_frontend_event)
        obs.script_log(obs.LOG_INFO, "{0} registered for frontend events".format(self))
        self.cutmode_handler = CutModeHandler(transitions)
        with self.leds as leds:
            leds.clear()
            self.update_jog_mode(JogMode.SCRL)
            self.live_overwrite = False
            self.duration = None
            self.last_duration_set = None
        self.settings_changed()

    def close(self):
        frontend_event.remove_frontend_event_listener(self.on_frontend_event)
        obs.script_log(obs.LOG_INFO, "{0} unregistered for frontend events".format(self))
        try:
            self.leds.off(BmdHidLed.TRANS | CutMode.leds() | all_cam_leds | BmdHidLed.LIVE_OWR)
            self.leds.off(JogMode.leds())
        except hid.HIDException:
            # we try to disable LEDs if we're still connected, if we're not, just abandon all hope
            pass
        super().close()
        self.on_close(self)

    def update_jog_mode(self, mode: JogMode):
        self.jog_mode = mode
        with self.leds as leds:
            leds.off(JogMode.leds())
            leds.on(mode.led())
        self.set_jog_mode(mode.mode())

    def get_current_cam(self) -> Optional[int]:
        scenes = obs.obs_frontend_get_scenes()
        scene_names = [obs.obs_source_get_name(scene) for scene in scenes]
        obs.source_list_release(scenes)
        if self.live_overwrite:
            scene = obs.obs_frontend_get_current_scene()
        else:
            scene = obs.obs_frontend_get_current_preview_scene()
        scene_name = obs.obs_source_get_name(scene)
        obs.obs_source_release(scene)
        index = scene_names.index(scene_name)
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
                obs.obs_frontend_preview_program_trigger_transition()

    def on_frontend_event(self, event: obs.FrontendEvent):
        if event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING:
            self.settings_changed()
        elif event == obs.OBS_FRONTEND_EVENT_TRANSITION_CHANGED:
            with self.leds as leds:
                leds.off(CutModeHandler.all_leds())
                leds.on(self.cutmode_handler.determine_status())
        elif event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
            self.on_scene_changed()
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

    def on_key_down(self, key: BmdHidKey):
        obs.script_log(obs.LOG_DEBUG, "on_key_down: {0}".format(key.name))
        if key == BmdHidKey.SHTL:
            self.update_jog_mode(JogMode.SHTL)
        elif key == BmdHidKey.JOG:
            self.update_jog_mode(JogMode.JOG)
        elif key == BmdHidKey.SCRL:
            self.update_jog_mode(JogMode.SCRL)
        elif key in CutMode.keys():
            with self.leds as leds:
                leds.off(CutModeHandler.all_leds())
                leds.on(self.cutmode_handler.set_mode(CutMode.from_key(key)))
        elif key == BmdHidKey.TRANS:
            with self.leds as leds:
                leds.off(CutModeHandler.all_leds())
                leds.on(self.cutmode_handler.toggle_skip_transitions())
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
            obs.obs_frontend_preview_program_trigger_transition()
        else:
            obs.script_log(obs.LOG_INFO, "Unknown key: {0}".format(key.name))

    def on_key_up(self, key: BmdHidKey):
        if key == BmdHidKey.TRANS_DUR:
            self.set_jog_mode(self.jog_mode.mode())
            self.duration = None

    def on_battery(self, charging: bool, level: int):
        pass

    def settings_changed(self):
        obs.script_log(obs.LOG_INFO, "Settings updated")
        with self.leds as leds:
            leds.off(CutModeHandler.all_leds())
            leds.on(self.cutmode_handler.determine_status())
