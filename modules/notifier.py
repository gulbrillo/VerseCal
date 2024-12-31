# modules/notifier.py
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt5.QtGui import QFont

class NotificationWindow(QWidget):
    def __init__(self, message, parent=None):
        super().__init__(parent)

        # Frameless + Always-on-top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # Semi-transparent
        self.setWindowOpacity(0.87)

        layout = QVBoxLayout()
        self.label = QLabel(message)
        self.label.setStyleSheet(
            "color: white; "
            "background-color: rgba(0, 0, 0, 128); "  # Black background with 50% opacity
            "font-size: 14px; "
            "padding: 8px;"
        )
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Position in the top-right corner of the primary screen
        screens = QApplication.screens()
        if screens:
            screen_geometry = screens[0].geometry()
        else:
            screen_geometry = QApplication.desktop().availableGeometry()

        w, h = 300, 60
        x = screen_geometry.width() - w - 20
        y = 20
        self.setGeometry(x, y, w, h)

        # Use an instance attribute for QTimer to avoid garbage collection
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.handle_close)
        self.timer.start(5000)  # Close after 5 seconds

    def handle_close(self):
        print("Closing NotificationWindow...")
        self.close()

def display_notification(message):
    """
    Call this function from the main Qt thread.
    It creates a NotificationWindow and shows it.
    """
    print("[DEBUG] display_notification called with:", message)
    app = QApplication.instance()
    if not app:
        print("No QApplication instance found!")
        return

    win = NotificationWindow(message)
    win.show()
    win.raise_()
    win.activateWindow()

    # Keep a reference to prevent garbage collection
    if not hasattr(app, '_notifications'):
        app._notifications = []
    app._notifications.append(win)

    # Remove reference after the window is closed
    win.destroyed.connect(lambda: app._notifications.remove(win))
