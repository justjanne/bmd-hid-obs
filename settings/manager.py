from __future__ import annotations

import abc

import obspython as obs


class SettingsManager(abc.ABC):
    @abc.abstractmethod
    def properties(self, properties: obs.Properties): ...

    @abc.abstractmethod
    def defaults(self, data: obs.Data): ...
