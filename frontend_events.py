from __future__ import annotations

from typing import Callable

import obspython as obs

_listeners: list[Callable[[obs.FrontendEvent], None]] = []


def on_frontend_event_global(event: obs.FrontendEvent):
    for listener in _listeners:
        listener(event)


def add_frontend_event_listener(listener: Callable[[obs.FrontendEvent], None]):
    if listener not in _listeners:
        _listeners.append(listener)


def remove_frontend_event_listener(listener: Callable[[obs.FrontendEvent], None]):
    if listener in _listeners:
        _listeners.append(listener)
