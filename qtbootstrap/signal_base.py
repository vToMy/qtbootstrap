from typing import Callable


class Signal:
    def __init__(self, *args, name: str = None):
        self.args = args
        self.name = name
        self.slots: list[Callable] = []

    def emit(self, *args, **kwargs):
        for slot in self.slots:
            slot(*args, **kwargs)

    def connect(self, slot: Callable):
        if slot not in self.slots:
            self.slots.append(slot)

    def disconnect(self, slot: Callable):
        if slot in self.slots:
            self.slots.remove(slot)

    def __iadd__(self, slot: Callable):
        self.connect(slot)
        return self

    def __isub__(self, slot: Callable):
        self.disconnect(slot)
        return self

    def __iter__(self):
        return iter(self.slots)

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = f'{owner.__qualname__}_{name}'
