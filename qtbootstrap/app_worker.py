from qtbootstrap.app_base import ApplicationBase
from qtbootstrap.asyncio_worker import AsyncIOWorker


class ApplicationWithWorker(ApplicationBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asyncio_worker = AsyncIOWorker()

    def exec(self) -> int:
        self.asyncio_worker.start()
        return super().exec()

    def quit(self):
        quit_func = super().quit
        self.asyncio_worker.quit()
        self.asyncio_worker.finished.connect(quit_func)
