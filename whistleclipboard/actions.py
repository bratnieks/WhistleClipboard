from __future__ import annotations

import platform
import subprocess


class ActionExecutor:
    def __init__(self) -> None:
        self.platform = platform.system().lower()

    def copy(self) -> None:
        self._send_shortcut("c")

    def paste(self) -> None:
        self._send_shortcut("v")

    def _send_shortcut(self, key: str) -> None:
        if self.platform == "darwin":
            # Using AppleScript keeps the MVP dependency-light on macOS.
            script = f'tell application "System Events" to keystroke "{key}" using command down'
            subprocess.run(["osascript", "-e", script], check=True)
            return

        if self.platform == "linux":
            raise RuntimeError("Linux shortcut support is not implemented yet.")

        if self.platform == "windows":
            raise RuntimeError("Windows shortcut support is not implemented yet.")

        raise RuntimeError(f"Unsupported platform: {self.platform}")
