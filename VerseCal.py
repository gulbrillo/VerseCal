# VerseCal.py
import sys
import threading
import datetime
import time
import textwrap
from PyQt5 import QtCore, QtWidgets, QtGui

# Import from our modules package
from modules.clipboard_monitor import ClipboardMonitor, COORDINATES_PATTERN
from modules.notifier import display_notification

class AppBridge(QtCore.QObject):
    """
    A helper class that defines a PyQt signal for new coordinates.
    We'll emit this signal from the background thread, and the main
    thread will show the popup.
    """
    # Updated to emit both str and float
    newCoordinates = QtCore.pyqtSignal(str, float)

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
        print("[DEBUG] Exit action triggered.")
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
    def on_new_item(coords_text, corrected_time_ms):
        print(f"[DEBUG] New coordinates detected: {coords_text}")
        print(f"[DEBUG] Corrected Timestamp (ms): {corrected_time_ms:.3f}")

        # Parse the coordinates using the imported COORDINATES_PATTERN
        match = COORDINATES_PATTERN.match(coords_text)
        if not match:
            print("[DEBUG] Clipboard text did not match the pattern.")
            return

        x_str, y_str, z_str = match.groups()

        # Convert captured strings to floats to remove any extra characters
        try:
            x = float(x_str)
            y = float(y_str)
            z = float(z_str)
        except ValueError as e:
            print(f"[DEBUG] Error converting coordinates to float: {e}")
            return

        # Format the float values consistently
        x_formatted = f"{x:.2f}"
        y_formatted = f"{y:.2f}"
        z_formatted = f"{z:.3f}"

        # Convert corrected_time_ms back to seconds for datetime
        corrected_time_sec = corrected_time_ms / 1000.0
        dt = datetime.datetime.fromtimestamp(corrected_time_sec).astimezone()
        formatted_time = dt.isoformat(timespec='milliseconds')  # ISO 8601 format with milliseconds and timezone

        # Construct the HTML-formatted message using a table for precise alignment
        message = textwrap.dedent(f"""
            <div style="text-align: right;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td colspan="2" style="text-align: right; color: #339fd1 !important;"><b>LOCATION LOGGED</b></td></tr>
                    <tr><td colspan="2" style="height: 10px;"></td></tr> <!-- Empty row for spacing -->
                    <tr><td colspan="2" style="text-align: right;"><b>Timestamp:</b></td></tr>
                    <tr><td colspan="2" style="text-align: right;">{corrected_time_ms:.3f} ms</td></tr>
                    <tr><td colspan="2" style="text-align: right;">{formatted_time}</td></tr>
                    <tr><td colspan="2" style="height: 10px;"></td></tr> <!-- Empty row for spacing -->
                    <tr><td colspan="2" style="text-align: right;"><b>Coordinates:</b></td></tr>
                    <tr><td style="text-align: right;">x =&nbsp;</td><td style="text-align: right;">{x_formatted}</td></tr>
                    <tr><td style="text-align: right;">y =&nbsp;</td><td style="text-align: right;">{y_formatted}</td></tr>
                    <tr><td style="text-align: right;">z =&nbsp;</td><td style="text-align: right;">{z_formatted}</td></tr>
                </table>
            </div>
        """)

        # Pass the formatted message to the notifier along with corrected_time_ms
        bridge.newCoordinates.emit(message, corrected_time_ms)

    monitor.on_new_item = on_new_item

    # Start monitor in background thread
    monitor_thread = threading.Thread(target=monitor.run, daemon=True)
    monitor_thread.start()
    print("[DEBUG] ClipboardMonitor thread started.")

    # Create system tray icon (use your .ico file from assets)
    tray_icon = SystemTrayApp(QtGui.QIcon("assets/icon.ico"), monitor, bridge)
    tray_icon.show()
    print("[DEBUG] System tray icon created and shown.")

    # Keep a reference to the tray icon to prevent garbage collection
    app.tray_icon = tray_icon

    # Run the application event loop
    print("[DEBUG] Starting Qt event loop.")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
