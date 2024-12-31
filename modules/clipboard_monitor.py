# modules/clipboard_monitor.py
import re
import time
import datetime
import ntplib
import win32clipboard
import win32con

# Regex to match lines of the form:
# Coordinates: x:<float> y:<float> z:<float>
COORDINATES_PATTERN = re.compile(
    r"^Coordinates:\s*x:([+-]?\d+(?:\.\d+)?)\s*y:([+-]?\d+(?:\.\d+)?)\s*z:([+-]?\d+(?:\.\d+)?)$"
)

SYNC_INTERVAL = 3600  # 1 hour (NTP resync)

class ClipboardMonitor:
    """
    Monitors the Windows clipboard for text of the form:
      Coordinates: x:<float> y:<float> z:<float>
    If matched, logs it with a millisecond-resolution Unix timestamp,
    corrected by an NTP offset (periodically refreshed).
    """

    def __init__(self, server="pool.ntp.org", log_file="coordinates.txt"):
        self.server = server
        self.log_file = log_file
        self.running = False
        self.offset = 0.0
        self.previous_text = ""
        self.last_sync_time = 0

        # This callback is called whenever a new matching text is logged
        self.on_new_item = None

    def get_ntp_offset(self, attempts=3):
        """
        Query the given NTP server multiple times to compute an average offset.
        offset = how many seconds we need to add to local time to match server time.
        Returns float or None if all attempts fail.
        """
        c = ntplib.NTPClient()
        offsets = []

        for _ in range(attempts):
            try:
                response = c.request(self.server, version=3)
                offsets.append(response.offset)
            except Exception:
                pass

        if offsets:
            return sum(offsets) / len(offsets)
        return None

    def sync_time(self):
        """Attempt to sync time with NTP and update self.offset."""
        new_offset = self.get_ntp_offset(attempts=5)
        if new_offset is not None:
            self.offset = new_offset
            print(f"[{datetime.datetime.utcnow()}] NTP offset re-synced: {self.offset:.6f} seconds")
        else:
            print("NTP offset re-sync failed. Retaining old offset.")

    def get_clipboard_text(self):
        """Safely open the clipboard, read its text content, return or empty."""
        text = ""
        try:
            win32clipboard.OpenClipboard()
            text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
        except Exception:
            pass
        finally:
            win32clipboard.CloseClipboard()
        return text

    def run(self):
        """Main polling loop (should be run in a background thread)."""
        # Initial NTP sync
        initial_offset = self.get_ntp_offset(attempts=5)
        if initial_offset is not None:
            self.offset = initial_offset
            print(f"Initial NTP offset: {self.offset:.6f} seconds")
        else:
            print("Initial NTP sync failed. Using local time only.")

        self.last_sync_time = time.time()
        self.running = True

        while self.running:
            now = time.time()

            # Periodic offset resync
            if now - self.last_sync_time >= SYNC_INTERVAL:
                self.sync_time()
                self.last_sync_time = now

            # Check the clipboard
            clipboard_text = self.get_clipboard_text()

            # If it's new + matches the pattern
            if (
                clipboard_text
                and clipboard_text != self.previous_text
                and COORDINATES_PATTERN.match(clipboard_text)
            ):
                corrected_time_ms = (now + self.offset) * 1000.0  # Float milliseconds

                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"{corrected_time_ms:.3f} {clipboard_text}\n")

                self.previous_text = clipboard_text

                # Invoke our callback (main thread will do the popup)
                if self.on_new_item:
                    self.on_new_item(clipboard_text, corrected_time_ms)

            time.sleep(1)

    def stop(self):
        """Stop the monitoring loop gracefully."""
        self.running = False
