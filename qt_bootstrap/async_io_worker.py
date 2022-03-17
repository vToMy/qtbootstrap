import asyncio
import logging
import threading
from concurrent.futures import Future
from typing import Callable, Coroutine

from PySide6 import QtCore
from PySide6.QtCore import QObject, Qt, QMutex, QMutexLocker, QThread


class AsyncIOWorker(QObject):

    finished = QtCore.Signal()

    def __init__(self, loop: asyncio.AbstractEventLoop = None, thread: QThread = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.loop = loop if loop is not None else asyncio.new_event_loop()
        self.asyncio_thread = thread if thread is not None else QThread()
        self.moveToThread(self.asyncio_thread)
        self.signals = dict()
        self.mutex = QMutex()
        self.mutex_locker = QMutexLocker(self.mutex)
        self._signals_added = False

    def start(self):
        self._finalize_connected_signals()
        self.asyncio_thread.started.connect(self.run)
        self.asyncio_thread.finished.connect(self.asyncio_thread.deleteLater)
        self.asyncio_thread.start()

    def run(self):
        if self.thread().objectName():
            threading.current_thread().name = self.thread().objectName()
        self.logger.debug('%s started', self.thread().objectName())
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.finished.emit()
            self.logger.debug('%s finished', self.thread().objectName())

    def stop(self):
        with self.mutex_locker:
            self.logger.debug('Stopping %s', self.asyncio_thread.objectName())
            self.loop.call_soon_threadsafe(self.loop.stop)

    def quit(self):
        self.logger.debug('Quitting %s', self.asyncio_thread.objectName())
        self.asyncio_thread.quit()

    def wait(self, *args, **kwargs):
        self.logger.debug('Waiting for %s', self.asyncio_thread.objectName())
        self.asyncio_thread.wait(*args, **kwargs)

    def create_task(self, coroutine: Coroutine, log_exception=True) -> Future:
        with self.mutex_locker:
            future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
            if log_exception:
                future.add_done_callback(self._on_future_done)
            return future

    def call_soon(self, func, *args):
        with self.mutex_locker:
            self.loop.call_soon_threadsafe(func, *args)

    def _on_future_done(self, future: Future):
        if future.cancelled():
            self.logger.debug('Cancelled future: %s', future)
            return
        if exception := future.exception():
            self.loop.call_exception_handler({
                'message': '',
                'exception': exception
            })

    def connect_signal(self, signal, slot: Callable):
        if self._signals_added:
            raise Exception('All signals must be connected before starting the worker')
        if signal.name is None:
            raise Exception('Signal must have a name')
        if signal.name in self.signals:
            if self.signals[signal.name][0] != signal:
                raise Exception(f'Signal name is not globally unique: {signal.name}')
            self.signals[signal.name][1].append(slot)
        else:
            self.signals[signal.name] = signal, [slot]

    def _finalize_connected_signals(self):
        self.__class__ = type(self.__class__.__name__, self.__class__.__bases__,
                              {**self.__class__.__dict__,
                               **{signal.name: QtCore.Signal(*signal.args) for signal, _ in self.signals.values()}}, )

        for signal, slots in self.signals.values():
            qt_signal = getattr(self, signal.name)
            for slot in slots:
                qt_signal.connect(slot, Qt.QueuedConnection)
            signal.connect(qt_signal.emit)
        self._signals_added = True
