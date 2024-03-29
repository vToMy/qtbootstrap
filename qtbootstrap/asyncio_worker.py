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
        self.setObjectName(self.__class__.__name__)
        if loop:
            self.loop = loop
        else:
            self.loop = asyncio.new_event_loop()
            self.loop.set_exception_handler(self._exception_handler)
        if thread:
            self.asyncio_thread = thread
        else:
            self.asyncio_thread = QThread()
            self.asyncio_thread.setObjectName(self.__class__.__name__ + 'Thread')
        self.moveToThread(self.asyncio_thread)
        self.signals = dict()
        self.mutex = QMutex()
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
        finally:
            self._handle_loop_close()
            self.finished.emit()
            self.logger.debug('%s finished', self.thread().objectName())

    def quit(self):
        with QMutexLocker(self.mutex):
            self.logger.debug('Stopping %s', self.thread().objectName())
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.logger.debug('Quitting %s', self.thread().objectName())
        self.asyncio_thread.quit()

    def wait(self, *args, **kwargs):
        self.logger.debug('Waiting for %s', self.thread().objectName())
        self.asyncio_thread.wait(*args, **kwargs)

    def create_task(self, coroutine: Coroutine, log_exception=True) -> Future:
        with QMutexLocker(self.mutex):
            future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
            if log_exception:
                future.add_done_callback(self._on_future_done)
            return future

    def call_soon(self, func, *args):
        with QMutexLocker(self.mutex):
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

    def _handle_loop_close(self):
        """ copied from asyncio.run source code """
        try:
            self._cancel_all_tasks()
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.run_until_complete(self.loop.shutdown_default_executor())
        finally:
            self.loop.close()

    def _cancel_all_tasks(self):
        """ copied from asyncio.run source code """
        to_cancel = asyncio.all_tasks(self.loop)
        if not to_cancel:
            return

        for task in to_cancel:
            task.cancel()

        self.loop.run_until_complete(asyncio.gather(*to_cancel, return_exceptions=True))

        for task in to_cancel:
            if task.cancelled():
                continue
            if task.exception() is not None:
                self.loop.call_exception_handler(
                    {
                        "message": "unhandled exception during asyncio.run() shutdown",
                        "exception": task.exception(),
                        "task": task,
                    }
                )

    def _exception_handler(self, loop, context):
        self.logger.error('Uncaught exception: %s', context.get('message'), exc_info=context.get('exception'))
