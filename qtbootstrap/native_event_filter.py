import platform

import shiboken6

if platform.system() == 'Windows':
    import ctypes
    import ctypes.wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, Signal


class NativeEventFilter(QAbstractNativeEventFilter):

    def __init__(self, message_to_signal: dict[int, Signal]):
        super().__init__()
        self.message_to_signal = message_to_signal

    def nativeEventFilter(self, event_type: bytes, message: shiboken6.Shiboken.VoidPtr):
        if event_type == b'windows_generic_MSG':
            msg = ctypes.wintypes.MSG.from_address(int(message))
            signal = self.message_to_signal.get(msg.message, None)
            if signal:
                signal.emit(msg)
