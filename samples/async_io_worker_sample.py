import sys

from PySide6.QtWidgets import QPushButton

from qt_bootstrap.app_base import ApplicationBase
from qt_bootstrap import signal_base
from qt_bootstrap.async_io_worker import AsyncIOWorker


class SampleClass:
    # you can use signals without specifying a name only at class-level:
    # * the name will be auto-generated based on the variable name.
    # * the variable name must be globally unique! (otherwise, please specify unique name using a keyword argument)
    # notice this is a minimal pure-python signal, not a qt signal, so you decouple your logic from qt
    sample_signal = signal_base.Signal(str)

    async def sample_task(self):
        print('task running')
        self.sample_signal.emit('Run task again')


class SampleApp(ApplicationBase):
    def quit(self):
        worker.stop()
        worker.quit()
        worker.wait()
        app.processEvents()  # process handling of worker finished signal before quiting
        super().quit()


class SampleButton(QPushButton):
    def closeEvent(self, event):
        app.quit()


if __name__ == '__main__':
    app = SampleApp()
    worker = AsyncIOWorker()
    sample_instance = SampleClass()
    widget = SampleButton('Run task')

    worker.finished.connect(lambda: print('worker finished'))
    app.sigint.connect(app.quit)
    # gui thread -> asyncio thread
    widget.pressed.connect(lambda: worker.create_task(sample_instance.sample_task()))
    # asyncio thread -> gui thread
    worker.connect_signal(sample_instance.sample_signal, lambda text: widget.setText(text))

    widget.show()
    worker.start()
    sys.exit(app.exec())
