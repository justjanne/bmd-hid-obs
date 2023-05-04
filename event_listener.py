from __future__ import annotations

from typing import Generic, ParamSpec, Callable

E = ParamSpec("E")


class EventListener(Generic[E]):
    _listener: list[Callable[E, None]]

    def __init__(self):
        self._listener = []

    def add_listener(self, listener: Callable[E, None]):
        self._listener.append(listener)

    def remove_listener(self, listener: Callable[E, None]):
        self._listener.remove(listener)

    def on_event(self, event: E):
        for listener in self._listener:
            listener(event)
