import logging
import signal

from PySide6 import QtCore
from PySide6.QtCore import Signal, QTextStream, QTimer
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtNetwork import QLocalSocket, QLocalServer


class ApplicationBase(QApplication):

    SIGNALS_TIMER_INTERVAL_MS = 500

    message_received = Signal(str)
    new_connection = Signal()
    sigint = Signal()

    def __init__(self, id_=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_signals()

        self.logger = logging.getLogger(__name__)
        self._id = id_

        if self._id:
            # Is there another instance running?
            self._out_socket = QLocalSocket()
            self._out_socket.connectToServer(self._id)
            self._is_running = self._out_socket.waitForConnected()

            if self._is_running:
                # Yes, there is.
                self._outStream = QTextStream(self._out_socket)
            else:
                # No, there isn't.
                self._out_socket = None
                self._outStream = None
                self._in_socket = None
                self._in_stream = None
                self._server = QLocalServer()
                self._server.removeServer(self._id)
                if not self._server.listen(self._id):
                    self.logger.warning('Cannot listen to other instances')
                self._server.newConnection.connect(self._on_new_connection)

    @property
    def is_running(self):
        """ Is another instance of this app already running? """
        return self._is_running

    @property
    def id(self):
        """ Unique id for the app, used to identify if the app is already running """
        return self._id

    def send_message(self, msg):
        if not self._outStream:
            return False
        self._outStream << msg << '\n'
        self._outStream.flush()
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

    def _setup_signals(self):
        signal.signal(signal.SIGINT, lambda *args: self.sigint.emit())
        # this noop timer is needed for sigint processing to work: https://stackoverflow.com/a/4939113
        timer = QTimer(self)
        timer.timeout.connect(lambda: None)
        timer.setInterval(self.SIGNALS_TIMER_INTERVAL_MS)
        timer.start()

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