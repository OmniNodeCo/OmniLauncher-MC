import traceback
import datetime
import uuid
from tkinter.messagebox import showerror

def handle_error(exception):
    # Step 1 — Generate unique ID
    error_id = uuid.uuid4()  # Research: uuid.uuid4()
    
    # Step 2 — Get current time
    current_time = datetime.datetime.now()  # Research: datetime.datetime.now()
    
    # Step 3 — Get error type name
    error_type = type(exception).__name__
    
    # Step 4 — Get full traceback
    full_details = traceback.format_exc()  # Research: traceback.format_exc()
    
    # Step 5 — Build log entry
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
    
    # Step 6 — Write to log file
    with open("launcher.log", "a") as file:  # Research: "a" mode for append
        file.write(log_entry)
    
    # Step 7 — Show popup to user
    showerror(
        "Error",  # Title
          f"An error occurred.\nError ID: {error_id}\nPlease report this on Github."  # Message including error_id
    )
    
    # Step 8 — Return the ID in case caller needs it
    return error_id