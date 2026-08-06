"""Error handling service module - PySide6 compatible."""

import traceback
import datetime
import uuid
import sys


def handle_error(exception: Exception, log_path: str = "launcher.log") -> uuid.UUID:
    """
    Handle an exception by logging it and showing an error dialog.

    Args:
        exception: The exception to handle.
        log_path: Path to the log file (default: "launcher.log").

    Returns:
        The unique error ID.
    """
    error_id = uuid.uuid4()
    current_time = datetime.datetime.now()
    error_type = type(exception).__name__
    full_details = traceback.format_exc()

    log_entry = f"""
=====================================
Error ID: {error_id}
Time: {current_time}
Error: {error_type}
Message: {exception}
Details:
{full_details}
=====================================
"""

    try:
        with open(log_path, "a", encoding="utf-8") as file:
            file.write(log_entry)
    except Exception:
        pass

    try:
        from PySide6.QtWidgets import QMessageBox, QApplication
        if QApplication.instance():
            QMessageBox.critical(
                None,
                "Error",
                f"An error occurred.\nError ID: {error_id}\nPlease report this on Github.",
            )
        else:
            print(f"Error {error_id}: {exception}", file=sys.stderr)
    except Exception:
        print(f"Error {error_id}: {exception}", file=sys.stderr)

    return error_id
