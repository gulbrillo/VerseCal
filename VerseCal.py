# VerseCal.py
import sys
import threading
from PyQt5 import QtCore, QtWidgets, QtGui

# Import from our modules package
from modules.clipboard_monitor import ClipboardMonitor
from modules.notifier import display_notification

class AppBridge(QtCore.QObject):
    """
    A helper class that defines a PyQt signal for new coordinates.
    We'll emit this signal from the background thread, and the main
    thread will show the popup.
    """
    newCoordinates = QtCore.pyqtSignal(str)

class SystemTrayApp(QtWidgets.QSystemTrayIcon):
    """
    System tray icon with a right-click menu to exit the app.
    """

    def __init__(self, icon, monitor, bridge, parent=None):
        super().__init__(icon, parent)
        self.monitor = monitor
        self.bridge = bridge

        # Build the tray menu
        menu = QtWidgets.QMenu(parent)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.exit_app)
        self.setContextMenu(menu)

        self.setToolTip("Clipboard Monitor (Coordinates)")

    def exit_app(self):
        """Stop the monitor thread and quit the application."""
        self.monitor.stop()
        QtWidgets.QApplication.quit()

def main():
    app = QtWidgets.QApplication(sys.argv)

    # Prevent the application from quitting when the last window is closed
    app.setQuitOnLastWindowClosed(False)

    # Create the AppBridge instance
    bridge = AppBridge()

    # Connect the signal to the display_notification slot
    bridge.newCoordinates.connect(display_notification)

    # Create the ClipboardMonitor
    monitor = ClipboardMonitor(log_file="coordinates.txt")

    # Define what happens when the monitor finds a new item
    def on_new_item(coords_text):
        print(f"[DEBUG] New coordinates detected: {coords_text}")
        bridge.newCoordinates.emit(coords_text)

    monitor.on_new_item = on_new_item

    # Start monitor in background thread
    monitor_thread = threading.Thread(target=monitor.run, daemon=True)
    monitor_thread.start()

    # Create system tray icon (use your .ico file from assets)
    tray_icon = SystemTrayApp(QtGui.QIcon("assets/icon.ico"), monitor, bridge)
    tray_icon.show()

    # Keep a reference to the tray icon to prevent garbage collection
    app.tray_icon = tray_icon

    # Run the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
