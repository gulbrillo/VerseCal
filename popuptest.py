import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import QTimer, Qt

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Frameless + Always-on-top:
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # A known, visible area on your main monitor:
        self.setGeometry(100, 100, 300, 100)

        label = QLabel("Hello, I'm visible!", self)
        label.move(10, 10)

        # Store QTimer in an instance attribute to avoid GC issues
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.handle_close)
        self.timer.start(3000)  # 3s

    def handle_close(self):
        print("Closing TestWindow...")
        self.close()

def main():
    app = QApplication(sys.argv)

    w = TestWindow()
    w.show()
    # Raise to front and try to activate
    w.raise_()
    w.activateWindow()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
