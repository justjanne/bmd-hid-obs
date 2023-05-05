from __future__ import annotations

import __venv__ as venv
import obspython as obs

from devices import DeviceManager
from events.frontend_event import on_frontend_event_global
from settings.transitions import TransitionSettings

if not venv.activated:
    raise RuntimeError("Not running in venv, aborting")

transition_settings = TransitionSettings()
device_manager = DeviceManager(transition_settings)


def script_description() -> str:
    return "BMD HID Device Support v0.0.1"


def script_load(settings: obs.Data):
    transition_settings.update(settings)
    device_manager.settings_changed()
    device_manager.update_devices()
    obs.timer_add(device_manager.poll_input, 1)
    obs.timer_add(device_manager.update_devices, 1000)
    obs.obs_frontend_add_event_callback(on_frontend_event_global)


def script_unload():
    obs.timer_remove(device_manager.poll_input)
    obs.timer_remove(device_manager.update_devices)
    obs.obs_frontend_remove_event_callback(on_frontend_event_global)
    device_manager.close()


def script_defaults(settings: obs.Data):
    transition_settings.defaults(settings)


def script_save(settings: obs.Data):
    pass


def script_update(settings: obs.Data):
    transition_settings.update(settings)
    device_manager.settings_changed()
    device_manager.update_devices()


def script_properties() -> obs.Properties:
    properties = obs.obs_properties_create()
    transition_settings.properties(properties)
    return properties


def update_devices(): device_manager.update_devices()


def poll_input(): device_manager.poll_input()


def close(): device_manager.close()
