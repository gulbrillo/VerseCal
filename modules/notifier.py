# modules/notifier.py
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt5.QtGui import QFont

class NotificationWindow(QWidget):
    def __init__(self, message, parent=None):
        super().__init__(parent)

        # Frameless + Always-on-top + Tool window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        # Enable transparent background
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Ensure no border via stylesheet
        self.setStyleSheet("background: transparent; border: none;")

        # Setup layout without margins and spacing
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove layout margins
        layout.setSpacing(0)  # Remove layout spacing

        # Label setup
        self.label = QLabel(message)
        self.label.setStyleSheet(
            "color: white; "
            "background-color: rgba(0, 0, 0, 128); "  # Semi-transparent black background
            "border: 1px solid rgba(255, 255, 255, 128); "  # 1px white border with 50% opacity
            "font-size: 14px; "
            "padding: 8px;"
        )
        self.label.setWordWrap(True)  # Enable text wrapping
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Align text to the left and center vertically

        layout.addWidget(self.label)
        self.setLayout(layout)

        # Position in the top-right corner of the primary screen with 20px gap
        screens = QApplication.screens()
        if screens:
            screen_geometry = screens[0].geometry()
        else:
            screen_geometry = QApplication.desktop().availableGeometry()

        window_width = 300
        window_height = 60  # Initial height; will adjust based on content

        # Calculate x and y for top-right corner with 20px gap
        x = screen_geometry.x() + screen_geometry.width() - window_width - 20
        y = screen_geometry.y() + 20  # 20px from the top

        self.setGeometry(x, y, window_width, window_height)

        # Adjust window height based on content
        self.adjustSizeBasedOnContent()

        # Timer to auto-close the window after 5 seconds
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.handle_close)
        self.timer.start(5000)  # 5000 milliseconds = 5 seconds

    def adjustSizeBasedOnContent(self):
        """
        Adjust the window's height based on the label's content to prevent text overflow.
        """
        # Calculate the height required for the label's content
        self.label.adjustSize()
        required_height = self.label.sizeHint().height() + 16  # 8px padding top and bottom

        # Set a maximum height to prevent the window from becoming too tall
        max_height = 200
        if required_height > max_height:
            required_height = max_height
            self.label.setFixedHeight(max_height - 16)  # Adjust label height accordingly

        # Update window height while keeping x and y positions fixed
        current_geometry = self.geometry()
        self.setGeometry(current_geometry.x(), current_geometry.y(), current_geometry.width(), required_height)

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

    # Create and show the notification window
    win = NotificationWindow(message)
    win.show()
    win.raise_()
    win.activateWindow()

    # Keep a reference to prevent garbage collection
    if not hasattr(app, '_notifications'):
        app._notifications = []
    app._notifications.append(win)

    # Remove the reference once the window is destroyed
    win.destroyed.connect(lambda: app._notifications.remove(win))
