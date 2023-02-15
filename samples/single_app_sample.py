import sys
from PySide6.QtWidgets import QWidget

from qtbootstrap.app_base import ApplicationBase

if __name__ == '__main__':
    appGuid = 'F3FF80BA-BA05-4277-8063-82A6DB9245A2'
    app = ApplicationBase(id_=appGuid)
    if app.is_running:
        print("The window is already displayed. Sending a message and quiting.")
        app.send_message('hello from another instance')
        sys.exit(0)
    # activate running app when trying to run a new instance
    app.new_connection.connect(lambda: app.activate_widget(widget))
    app.message_received.connect(lambda message: print(f'received message from another instance: {message}'))
    app.sigint.connect(app.quit)
    app.query_end_session.connect(app.quit)

    widget = QWidget()
    widget.show()
    sys.exit(app.exec())
