"""Windows COM apartment initialization context manager for thread safety."""

import sys


class COMContext:
    """Ensures pythoncom.CoInitialize() is invoked on Windows threads."""

    def __enter__(self) -> None:
        if sys.platform == "win32":
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if sys.platform == "win32":
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass
