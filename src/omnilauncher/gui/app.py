"""OmniLauncher-MC main application window."""

import json
import os
import shutil
import tkinter
import tkinter.messagebox
from tkinter import ttk
from tkinter.messagebox import askquestion

import minecraft_launcher_lib

from omnilauncher.services import get_latest_version, get_release_versions, launch
import omnilauncher.services.launcher as launcher_state


def _project_root() -> str:
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


PROJECT_ROOT = _project_root()
SETTINGS_FILE = os.path.join(PROJECT_ROOT, "settings.json")
LOG_FILE = os.path.join(PROJECT_ROOT, "launcher.log")


class OmniLauncherApp:
    """Main application window for OmniLauncher-MC."""

    def __init__(self) -> None:
        self.root = tkinter.Tk()
        self.root.title("OmniLauncher-MC")
        self.root.geometry("600x600")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._notebook = ttk.Notebook(self.root)
        self._notebook.pack(fill="both", expand=True)

        self._launcher_tab = ttk.Frame(self._notebook)
        self._about_tab = ttk.Frame(self._notebook)
        self._settings_tab = ttk.Frame(self._notebook)
        self._console_tab = ttk.Frame(self._notebook)

        self._notebook.add(self._launcher_tab, text="Launcher")
        self._notebook.add(self._about_tab, text="About")
        self._notebook.add(self._settings_tab, text="Settings")
        self._notebook.add(self._console_tab, text="Console")

        self._settings = self._load_settings()

        self._username_var = tkinter.StringVar(value=self._settings.get("username", "Steve"))
        self._selected_version = tkinter.StringVar()
        self._ram_slider: tkinter.Scale | None = None
        self._java_entry: tkinter.Entry | None = None
        self._version_combobox: ttk.Combobox | None = None
        self._error_log_text: tkinter.Text | None = None

        self._status_var = tkinter.StringVar(value="Ready")
        self._percent_var = tkinter.StringVar(value="0%")
        self._progress_var = tkinter.IntVar(value=0)

        self._process = None
        self._progress_bar: ttk.Progressbar | None = None
        self._console_text: tkinter.Text | None = None

        self._build_launcher_tab()
        self._build_about_tab()
        self._build_settings_tab()
        self._build_console_tab()

    # ---- Tab builders ----

    def _build_launcher_tab(self) -> None:
        t = self._launcher_tab

        tkinter.Button(t, text="Launch", command=self._on_launch_clicked).grid(
            row=0, column=0, padx=10, pady=5
        )
        tkinter.Button(t, text="Quit", command=self._ask_quit).grid(
            row=1, column=0, padx=10, pady=5
        )

        tkinter.Label(t, text="UserName").grid(row=2, column=0, padx=10, pady=5)
        tkinter.Entry(t, textvariable=self._username_var).grid(
            row=3, column=0, padx=10, pady=5
        )

        self._version_combobox = ttk.Combobox(
            t,
            textvariable=self._selected_version,
            values=get_release_versions(),
            state="readonly",
        )
        self._version_combobox.set(get_latest_version())
        self._version_combobox.grid(row=4, column=0, padx=10, pady=5)

        tkinter.Label(t, textvariable=self._status_var).grid(
            row=5, column=0, pady=5
        )

        self._progress_bar = ttk.Progressbar(
            t,
            variable=self._progress_var,
            maximum=100,
            length=300,
        )
        self._progress_bar.grid(row=6, column=0, padx=10, pady=5)

        tkinter.Label(t, textvariable=self._percent_var).grid(
            row=7, column=0, pady=2
        )

    def _build_about_tab(self) -> None:
        t = self._about_tab
        tkinter.Button(
            t,
            text="Open Changelog",
            command=lambda: self._open_text_file("Changelog", "Changelog.txt"),
        ).grid(row=0, column=0, padx=10, pady=5)
        tkinter.Button(
            t,
            text="Open Terms",
            command=lambda: self._open_text_file("Terms", "TERMS.txt"),
        ).grid(row=1, column=0, padx=10, pady=5)
        tkinter.Button(
            t,
            text="Open License",
            command=lambda: self._open_text_file("License", "LICENSE.txt"),
        ).grid(row=2, column=0, padx=10, pady=5)

    def _build_settings_tab(self) -> None:
        t = self._settings_tab

        tkinter.Label(t, text="RAM (GB)").grid(row=0, column=0, padx=10, pady=5)
        self._ram_slider = tkinter.Scale(t, from_=1, to=16, orient="horizontal")
        self._ram_slider.set(self._settings.get("ram", 4))
        self._ram_slider.grid(row=0, column=1, padx=10, pady=5)

        tkinter.Label(t, text="Java Path").grid(row=1, column=0, padx=10, pady=5)
        self._java_entry = tkinter.Entry(t)
        self._java_entry.grid(row=1, column=1, padx=10, pady=5)
        self._java_entry.insert(0, self._settings.get("java_path", ""))

        tkinter.Button(
            t, text="Delete ALL Data", bg="red", command=self._del_all_data
        ).grid(row=2, column=0, padx=10, pady=5)

        tkinter.Label(t, text="Error Log").grid(row=3, column=0, padx=10, pady=5)
        self._error_log_text = tkinter.Text(t, height=10, width=40, wrap="word")
        self._error_log_text.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        self._error_log_text.config(state="disabled")

        tkinter.Button(
            t, text="Refresh", command=self._refresh_error_log
        ).grid(row=5, column=0, sticky="e", padx=5)
        tkinter.Button(
            t, text="Copy", command=self._copy_error_log
        ).grid(row=5, column=1, sticky="w", padx=5)
        tkinter.Button(
            t, text="Clear Log", command=self._clear_error_log
        ).grid(row=5, column=2, sticky="w", padx=5)

    def _build_console_tab(self) -> None:
        t = self._console_tab

        self._console_text = tkinter.Text(
            t,
            wrap="word",
            bg="black",
            fg="white",
            font=("Courier", 10),
        )
        self._console_text.pack(fill="both", expand=True, padx=5, pady=5)
        self._console_text.config(state="disabled")

        tkinter.Button(
            t, text="Clear Console", command=self._clear_console
        ).pack(pady=5)

    # ---- Polling ----

    def _update_progress(self) -> None:
        self._status_var.set(launcher_state.current_status)

        if launcher_state.current_max > 0:
            percent = int(
                (launcher_state.current_progress / launcher_state.current_max) * 100
            )
        else:
            percent = 0

        self._progress_var.set(percent)
        self._percent_var.set(f"{percent}%")

        if launcher_state.current_status not in ("Done", "Ready"):
            self.root.after(100, self._update_progress)
        else:
            self._status_var.set("Ready")
            self._progress_var.set(0)
            self._percent_var.set("0%")

    def _update_console(self) -> None:
        if launcher_state.console_lines and self._console_text:
            self._console_text.config(state="normal")
            while launcher_state.console_lines:
                line = launcher_state.console_lines.pop(0)
                self._console_text.insert("end", line)
            self._console_text.see("end")
            self._console_text.config(state="disabled")

        if launcher_state.current_status not in ("Done", "Ready"):
            self.root.after(200, self._update_console)

    def _clear_console(self) -> None:
        if self._console_text:
            self._console_text.config(state="normal")
            self._console_text.delete("1.0", "end")
            self._console_text.config(state="disabled")

    # ---- Actions ----

    def _ask_quit(self) -> None:
        if askquestion("Message from OmniLauncher", "Are you sure you want to quit?") == "yes":
            self._on_closing()

    def _open_text_file(self, title: str, filename: str) -> None:
        filepath = os.path.join(PROJECT_ROOT, filename)
        top = tkinter.Toplevel()
        top.title(title)
        top.geometry("500x400")
        text = tkinter.Text(top, wrap="word")
        text.pack(fill="both", expand=True)
        with open(filepath, "r", encoding="utf-8") as f:
            text.insert("1.0", f.read())
        text.config(state="disabled")

    def _del_all_data(self) -> None:
        if askquestion("Warning", "Are you sure you want to delete all data?") == "yes":
            shutil.rmtree(minecraft_launcher_lib.utils.get_minecraft_directory())

    def _load_settings(self) -> dict:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        return {"username": "Steve", "ram": 4, "java_path": "", "last_version": ""}

    def _save_settings(self) -> None:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(
                {
                    "username": self._username_var.get(),
                    "ram": self._ram_slider.get() if self._ram_slider else 4,
                    "java_path": self._java_entry.get() if self._java_entry else "",
                    "last_version": self._version_combobox.get() if self._version_combobox else "",
                },
                f,
                indent=4,
            )

    def _on_launch_clicked(self) -> None:
        username = self._username_var.get()
        version = self._selected_version.get()
        ram = self._ram_slider.get() if self._ram_slider else 4

        if not username.strip():
            tkinter.messagebox.showwarning("Warning", "Username cannot be empty.")
            return

        if not version:
            tkinter.messagebox.showwarning("Warning", "Please select a version.")
            return

        self._clear_console()

        launch(username, version, ram)

        self._update_progress()
        self._update_console()

    def _refresh_error_log(self) -> None:
        if self._error_log_text is None:
            return
        self._error_log_text.config(state="normal")
        self._error_log_text.delete("1.0", "end")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                self._error_log_text.insert("1.0", f.read())
        else:
            self._error_log_text.insert("1.0", "No errors logged.")
        self._error_log_text.config(state="disabled")

    def _copy_error_log(self) -> None:
        if self._error_log_text is None:
            return
        content = self._error_log_text.get("1.0", "end")
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        tkinter.messagebox.showinfo("Copied", "Error log copied to clipboard.")

    def _clear_error_log(self) -> None:
        if askquestion("Warning", "Clear all error logs?") == "yes":
            with open(LOG_FILE, "w") as f:
                f.write("")
            self._refresh_error_log()

    def _on_closing(self) -> None:
        self._save_settings()
        self.root.destroy()

    # ---- Public API ----

    def run(self) -> None:
        """Start the main event loop."""
        self.root.mainloop()


def main() -> None:
    """Launch the OmniLauncher-MC application."""
    app = OmniLauncherApp()
    app.run()


if __name__ == "__main__":
    main()