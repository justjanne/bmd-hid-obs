from __future__ import annotations

from typing import Tuple

import hid
import obspython as obs
from bmd_hid_device.devices import BmdDevices, VID_BMD
from bmd_hid_device.util.deviceinfo import HidDeviceInfo

from bmd_device import ObsBmdDevice
from settings.transitions import TransitionSettings


class DeviceManager:
    _devices: list[ObsBmdDevice]
    _device_infos: list[HidDeviceInfo]
    _transition_settings: TransitionSettings

    def __init__(self, transition_settings: TransitionSettings):
        self._devices = []
        self._device_infos = []
        self._transition_settings = transition_settings

    def close(self):
        self._destroy_devices()

    def _destroy_devices(self):
        for device in self._devices:
            device.close()
        self._devices = []

    def _find_devices(self):
        tree: dict[Tuple[int, int], dict[str, HidDeviceInfo]] = {}
        for usb_id in BmdDevices:
            tree[usb_id] = {}

        entries: list[HidDeviceInfo] = hid.enumerate(vid=VID_BMD)
        for device in entries:
            usb_id = (device["vendor_id"], device["product_id"])
            if usb_id in tree:
                tree[usb_id][device["serial_number"]] = device
        return [info for device_dict in tree.values() for info in device_dict.values()]

    def _init_devices(self):
        for device_info in self._device_infos:
            try:
                self._devices.append(ObsBmdDevice(device_info, self._transition_settings, self._on_close))
            except hid.HIDException:
                # This means the device was likely removed during connection, let's remove it from the list
                self._device_infos.remove(device_info)
        if len(self._device_infos) == 0:
            obs.script_log(obs.LOG_WARNING, "could not find any BMD device")

    def _on_close(self, device: ObsBmdDevice):
        if device in self._devices:
            self._devices.remove(device)
        if device.device_info() in self._device_infos:
            self._device_infos.remove(device.device_info())

    def update_devices(self):
        device_infos = self._find_devices()
        if self._device_infos != device_infos:
            self._device_infos = device_infos
        current_devices = [device.device_info() for device in self._devices]
        if current_devices != device_infos:
            obs.script_log(obs.LOG_INFO, "Device list has changed: from {0} to {1}".format(
                [(i["vendor_id"], i["product_id"], i["serial_number"]) for i in device_infos],
                [(i["vendor_id"], i["product_id"], i["serial_number"]) for i in current_devices],
            ))
            self._destroy_devices()
            self._init_devices()

    def poll_input(self):
        for device in self._devices:
            if device.isclosed():
                if device in self._devices:
                    self._devices.remove(device)
                if device.device_info() in self._device_infos:
                    self._device_infos.remove(device.device_info())
            try:
                device.poll_available()
            except hid.HIDException as e:
                obs.script_log(obs.LOG_ERROR, "Error communicating with device: {0}".format(e))
                device.close()
                if device in self._devices:
                    self._devices.remove(device)
                if device.device_info() in self._device_infos:
                    self._device_infos.remove(device.device_info())

    def settings_changed(self):
        for device in self._devices:
            device.settings_changed()
