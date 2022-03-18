# Bootstrap for python QT apps

## Features
* Catch `sigint` signal (handle however you want).
* Single-instance app (with inter-instance communication).
* asyncio worker thread for background processing:
  * This is an alternative to [qasync](https://github.com/CabbageDevelopment/qasync).
  * Instead of the app running async, there 2 threads: GUI thread and asyncio thread.
  * This ensures that even if the asyncio thread is performing poorly, the GUI will not be affected.
  * Complete isolation of business logic and GUI.

## Samples
See the `samples` folder.
