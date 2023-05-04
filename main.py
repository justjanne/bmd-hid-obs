from __future__ import annotations

import obspython as obs
from bmd_hid_device.devices import DavinciSpeedEditor

from bmd_device import ObsBmdDevice
from frontend_events import on_frontend_event_global

_devices: list[ObsBmdDevice] = []


def _destroy_devices():
    obs.obs_frontend_remove_event_callback(on_frontend_event_global)
    for device in _devices:
        device.close()
    _devices.clear()


def _init_devices(settings: obs.Settings):
    obs.obs_frontend_add_event_callback(on_frontend_event_global)
    _devices.append(ObsBmdDevice(DavinciSpeedEditor))


def _device_tick():
    for device in _devices:
        if not device.isclosed():
            device.poll(1)


def script_description() -> str:
    return "BMD HID Device Support v0.0.1"


def script_load(settings: obs.Settings):
    _init_devices(settings)
    obs.timer_add(_device_tick, 1)


def script_unload():
    obs.timer_remove(_device_tick)
    _destroy_devices()


def script_defaults(settings: obs.Settings):
    pass


def script_save(settings: obs.Settings):
    pass


def script_update(settings: obs.Settings):
    _destroy_devices()
    _init_devices(settings)


def script_properties() -> obs.Properties:
    properties = obs.obs_properties_create()
    return properties


def script_tick(seconds: int):
    pass
