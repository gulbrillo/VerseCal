import sys
import threading
from PyQt5 import QtWidgets, QtGui
from modules.clipboard_monitor import ClipboardMonitor

class SystemTrayApp(QtWidgets.QSystemTrayIcon):
    """
    Creates a system tray icon with a context menu.
    When 'Exit' is clicked, we stop the ClipboardMonitor and quit.
    """

    def __init__(self, icon, monitor, parent=None):
        super().__init__(icon, parent)
        self.monitor = monitor

        # Create the tray icon menu
        menu = QtWidgets.QMenu(parent)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.exit_app)

        self.setContextMenu(menu)
        self.setToolTip("Clipboard Monitor (Coordinates)")

    def exit_app(self):
        """Stop the monitor and quit the application."""
        self.monitor.stop()           # Signal the monitor thread to stop
        QtWidgets.QApplication.quit()  # Quit the Qt event loop

def main():
    app = QtWidgets.QApplication(sys.argv)

    # 1) Create the clipboard monitor
    monitor = ClipboardMonitor(log_file="coordinates.txt")

    # 2) Run it in a background thread
    monitor_thread = threading.Thread(target=monitor.run, daemon=True)
    monitor_thread.start()

    # 3) Create the system tray icon
    tray_icon = SystemTrayApp(QtGui.QIcon("assets/icon.ico"), monitor)
    tray_icon.show()

    # 4) Run the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
