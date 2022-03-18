# Bootstrap for python QT apps

## Features
* Catch `sigint` signal (handle however you want).
* Single-instance app (with inter-instance communication).
* asyncio worker thread for background processing:
  * This is an alternative to [qasync](https://github.com/CabbageDevelopment/qasync).  
    Instead of the whole app running async in a single thread, there 2 threads:
    * GUI thread (with QT event loop).
    * asyncio thread (with python's event loop).

    This ensures that even if the asyncio thread is performing poorly, the GUI will not be affected.
  * Complete isolation of business logic from GUI.
* Cross-platform.

## Samples
See the `samples` folder.
