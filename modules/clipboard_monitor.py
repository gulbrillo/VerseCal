import re
import time
import datetime
import threading
import ntplib
import win32clipboard
import win32con

# Regex to match lines of the form:
# Coordinates: x:<float> y:<float> z:<float>
# Floats can be +/- with optional decimals.
COORDINATES_PATTERN = re.compile(
    r"^Coordinates:\s*x:([+-]?\d+(?:\.\d+)?)\s*y:([+-]?\d+(?:\.\d+)?)\s*z:([+-]?\d+(?:\.\d+)?)$"
)

# How often (in seconds) to re-synchronize with NTP
SYNC_INTERVAL = 3600  # 1 hour

class ClipboardMonitor:
    """
    Monitors the Windows clipboard for text of the form:
      Coordinates: x:<float> y:<float> z:<float>
    If matched, logs it with a millisecond-resolution Unix timestamp
    that's corrected by an NTP offset (periodically refreshed).
    """

    def __init__(self, server="pool.ntp.org", log_file="clipboard_log.txt"):
        self.server = server
        self.log_file = log_file
        self.running = False    # Controls the polling loop
        self.offset = 0.0       # Time offset (NTP-based)
        self.previous_text = "" # Last clipboard text we logged
        self.last_sync_time = 0 # For periodic re-sync

    def get_ntp_offset(self, attempts=3):
        """
        Query the given NTP server multiple times to compute an average offset.
        offset = how many seconds we need to add to local time to match server time.
        Returns float or None if all attempts fail.
        """
        import ntplib
        c = ntplib.NTPClient()
        offsets = []

        for _ in range(attempts):
            try:
                response = c.request(self.server, version=3)
                # ntplib calculates offset = server_time - local_time (factoring round-trip delay)
                offsets.append(response.offset)
            except Exception:
                pass

        if offsets:
            return sum(offsets) / len(offsets)
        return None

    def sync_time(self):
        """ Attempt to sync time with NTP and update self.offset. """
        new_offset = self.get_ntp_offset(attempts=5)
        if new_offset is not None:
            self.offset = new_offset
            print(f"[{datetime.datetime.utcnow()}] NTP offset re-synced: {self.offset:.6f} s")
        else:
            print("NTP offset re-sync failed. Retaining old offset.")

    def get_clipboard_text(self):
        """
        Open the clipboard and get the current text.
        Return empty string if it's not text or an error occurred.
        """
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
        """
        The main monitoring loop. Polls the clipboard every second,
        checks for matching text, logs if needed, and periodically
        re-syncs time.
        """
        # Initial NTP sync attempt
        offset = self.get_ntp_offset(attempts=5)
        if offset is not None:
            self.offset = offset
            print(f"Initial NTP offset: {self.offset:.6f} s")
        else:
            print("Initial NTP sync failed. Using local time only.")

        self.last_sync_time = time.time()
        self.running = True

        while self.running:
            current_time = time.time()

            # Re-sync if enough time passed
            if current_time - self.last_sync_time >= SYNC_INTERVAL:
                self.sync_time()
                self.last_sync_time = current_time

            # Check clipboard
            clipboard_text = self.get_clipboard_text()

            # If it's new and matches our pattern, log it
            if (
                clipboard_text
                and clipboard_text != self.previous_text
                and COORDINATES_PATTERN.match(clipboard_text)
            ):
                # Compute corrected time in ms
                corrected_time_ms = int((current_time + self.offset) * 1000)

                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"{corrected_time_ms} {clipboard_text}\n")

                self.previous_text = clipboard_text

            time.sleep(1)

    def stop(self):
        """ Stop the monitoring loop gracefully. """
        self.running = False
