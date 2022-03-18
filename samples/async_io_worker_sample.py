import logging
import sys

from PySide6.QtWidgets import QPushButton

from qtbootstrap import signal_base
from qtbootstrap.app_worker import ApplicationWithWorker


class SampleClass:
    # you can use signals without specifying a name only at class-level:
    # * the name will be auto-generated based on the variable name.
    # * the variable name must be globally unique! (otherwise, please specify unique name using a keyword argument)
    # notice this is a minimal pure-python signal, not a qt signal, so you decouple your logic from qt
    sample_signal = signal_base.Signal(str)

    async def sample_task(self):
        logging.debug('task running')
        self.sample_signal.emit('Run task again')


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(threadName)-19s - %(name)-27s - %(levelname)s - %(message)s',
                        level=logging.DEBUG)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

    app = ApplicationWithWorker()
    sample_instance = SampleClass()
    widget = QPushButton('Run task')
    widget.closeEvent = lambda event: app.quit()

    app.asyncio_worker.finished.connect(lambda: logging.debug('on %s finished',
                                                              app.asyncio_worker.asyncio_thread.objectName()))
    app.sigint.connect(app.quit)
    # gui thread -> asyncio thread
    widget.pressed.connect(lambda: app.asyncio_worker.create_task(sample_instance.sample_task()))
    # asyncio thread -> gui thread
    app.asyncio_worker.connect_signal(sample_instance.sample_signal, lambda text: widget.setText(text))
    widget.show()
    sys.exit(app.exec())
