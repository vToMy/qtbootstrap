import platform

import shiboken6

if platform.system() == 'Windows':
    import ctypes
    import ctypes.wintypes
    import win32con

from PySide6.QtCore import QAbstractNativeEventFilter, Signal


class NativeEventFilter(QAbstractNativeEventFilter):

    def __init__(self, query_end_session_signal: Signal, usb_connected_or_disconnected_signal: Signal):
        super().__init__()
        self.message_to_signal = {
            win32con.WM_DEVICECHANGE: usb_connected_or_disconnected_signal,
            # This message is being sent by the msi to terminate the program during installation
            # This ensures the program terminates gracefully to avoid errors during upgrade
            win32con.WM_QUERYENDSESSION: query_end_session_signal
        }

    def nativeEventFilter(self, event_type: bytes, message: shiboken6.Shiboken.VoidPtr):
        if event_type == b'windows_generic_MSG':
            msg = ctypes.wintypes.MSG.from_address(int(message))
            signal = self.message_to_signal.get(msg.message)
            if signal:
                signal.emit()
