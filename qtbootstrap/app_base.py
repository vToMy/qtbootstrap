import logging
import platform
import signal

from PySide6 import QtCore
from PySide6.QtCore import Signal, QTextStream, QTimer
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtNetwork import QLocalSocket, QLocalServer

from qtbootstrap.native_event_filter import NativeEventFilter


class ApplicationBase(QApplication):

    DEFAULT_SIGNALS_TIMER_INTERVAL_MS = 500

    message_received = Signal(str)
    new_connection = Signal()
    sigint = Signal()
    query_end_session_signal = Signal(object)
    end_session_signal = Signal(object)
    device_change_signal = Signal(object)

    def __init__(self, id_=None, signals_timer_interval_ms=DEFAULT_SIGNALS_TIMER_INTERVAL_MS,
                 auto_handle_close_events: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self._id = id_
        self.signals_timer_interval_ms = signals_timer_interval_ms
        self.native_event_filter = None
        if platform.system() == 'Windows':
            import win32con
            self.native_event_filter = NativeEventFilter(
                message_to_signal={
                    # https://learn.microsoft.com/en-us/windows/win32/shutdown/wm-queryendsession
                    win32con.WM_QUERYENDSESSION: self.query_end_session_signal,
                    # https://learn.microsoft.com/en-us/windows/win32/shutdown/wm-endsession
                    win32con.WM_ENDSESSION: self.end_session_signal,
                    win32con.WM_CLOSE: None,
                    win32con.WM_QUIT: None,
                    # https://learn.microsoft.com/en-us/windows/win32/devio/wm-devicechange
                    win32con.WM_DEVICECHANGE: self.device_change_signal
                })

        if self._id:
            # Is there another instance running?
            self._out_socket = QLocalSocket()
            self._out_socket.connectToServer(self._id)
            self._is_running = self._out_socket.waitForConnected()

            if self._is_running:
                # Yes, there is.
                self._out_stream = QTextStream(self._out_socket)
            else:
                # No, there isn't.
                self._out_socket = None
                self._out_stream = None
                self._in_socket = None
                self._in_stream = None
                self._server = QLocalServer()
                self._server.removeServer(self._id)
                if not self._server.listen(self._id):
                    self.logger.warning('Cannot listen to other instances')
                self._server.newConnection.connect(self._on_new_connection)
        if auto_handle_close_events:
            self._setup_close_events_signals()

    def exec(self) -> int:
        # setting the sigint signal just before starting the app, so we'll have access to the event loop
        self._setup_signals(self.signals_timer_interval_ms)
        return super().exec()

    @property
    def is_running(self):
        """ Is another instance of this app already running? """
        return self._is_running

    @property
    def id(self):
        """ Unique id for the app, used to identify if the app is already running """
        return self._id

    def send_message(self, msg):
        if not self._out_stream:
            return False
        self._out_stream << msg << '\n'
        self._out_stream.flush()
        return self._out_socket.waitForBytesWritten()

    def _on_new_connection(self):
        if self._in_socket:
            self._in_socket.readyRead.disconnect(self._on_ready_read)
        self._in_socket = self._server.nextPendingConnection()
        if not self._in_socket:
            return
        self._in_stream = QTextStream(self._in_socket)
        self._in_socket.readyRead.connect(self._on_ready_read)
        self.new_connection.emit()

    def _on_ready_read(self):
        while True:
            msg = self._in_stream.readLine()
            if not msg:
                break
            self.message_received.emit(msg)

    def _setup_signals(self, signals_timer_interval_ms):
        signal.signal(signal.SIGINT, lambda *args: self.sigint.emit())
        # this noop timer is needed for sigint processing to work: https://stackoverflow.com/a/4939113
        timer = QTimer(self)
        timer.timeout.connect(lambda: None)
        timer.setInterval(signals_timer_interval_ms)
        timer.start()
        if self.native_event_filter:
            self.installNativeEventFilter(self.native_event_filter)

    def activate_widget(self, widget: QWidget):
        # bring window to top and act like a "normal" window!
        # set always on top flag, makes window disappear
        widget.setWindowFlags(widget.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        # makes window reappear, but it's ALWAYS on top
        widget.show()
        # clear always on top flag, makes window disappear
        widget.setWindowFlags(widget.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
        # makes window reappear, acts like normal window now
        # (on top now but can be underneath if you raise another window)
        widget.show()

    def _setup_close_events_signals(self):
        self.sigint.connect(self.quit)
        self.end_session_signal.connect(lambda message: self.quit() if message.wParam else None)
