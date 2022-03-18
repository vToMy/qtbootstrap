from qtbootstrap.app_base import ApplicationBase
from qtbootstrap.asyncio_worker import AsyncIOWorker


class ApplicationWithWorker(ApplicationBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asyncio_worker = AsyncIOWorker()
        self.aboutToQuit.connect(self._on_about_to_quit)

    def exec(self) -> int:
        self.asyncio_worker.start()
        return super().exec()

    def _on_about_to_quit(self):
        self.asyncio_worker.quit()
        self.asyncio_worker.wait()
