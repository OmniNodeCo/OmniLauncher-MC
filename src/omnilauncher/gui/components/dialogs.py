"""Dialogs and popups."""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable


class CrashReportDialog(tk.Toplevel):
    def __init__(self, parent, theme: Dict[str, str], log_text: str, findings: list):
        super().__init__(parent)
        self.title("Crash Report • OmniLauncher")
        self.configure(bg=theme["bg"])
        self.geometry("640x520")
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text="💥  Minecraft Crashed", font=("Segoe UI", 14, "bold"), bg=theme["bg"], fg=theme["error"]).pack(anchor="w", padx=20, pady=(16, 4))
        tk.Label(self, text="Launcher analyzed the log and tried to explain what went wrong:", font=("Segoe UI", 9), bg=theme["bg"], fg=theme["text_secondary"]).pack(anchor="w", padx=20)

        # findings
        findings_frame = tk.Frame(self, bg=theme["card_bg"], highlightthickness=1, highlightbackground=theme["card_border"])
        findings_frame.pack(fill="x", padx=16, pady=12)

        if not findings:
            tk.Label(findings_frame, text="No specific cause found. Please check full log.", bg=theme["card_bg"], fg=theme["text_secondary"]).pack(padx=12, pady=12)
        else:
            for f in findings:
                sev = f.get("severity", "error")
                color = theme["error"] if sev in ("error", "critical") else theme["warning"] if sev == "warn" else theme["text_primary"]
                row = tk.Frame(findings_frame, bg=theme["card_bg"])
                row.pack(fill="x", padx=12, pady=6)
                tk.Label(row, text=f"[{sev.upper()}] {f['title']}", font=("Segoe UI", 10, "bold"), bg=theme["card_bg"], fg=color, anchor="w").pack(anchor="w")
                tk.Label(row, text=f["description"], font=("Segoe UI", 9), bg=theme["card_bg"], fg=theme["text_secondary"], wraplength=560, justify="left").pack(anchor="w", pady=2)
                tk.Label(row, text=f"Fix: {f['fix']}", font=("Segoe UI", 9, "bold"), bg=theme["card_bg"], fg=theme["text_primary"], wraplength=560, justify="left").pack(anchor="w")

        # log preview
        tk.Label(self, text="Log Snippet", font=("Segoe UI", 10, "bold"), bg=theme["bg"], fg=theme["text_primary"]).pack(anchor="w", padx=20, pady=(8, 4))
        txt = tk.Text(self, bg=theme["input_bg"], fg=theme["text_secondary"], height=12, font=("Consolas", 9), wrap="word", bd=0)
        txt.pack(fill="both", expand=True, padx=16, pady=4)
        txt.insert("1.0", log_text[-4000:] if len(log_text) > 4000 else log_text)
        txt.configure(state="disabled")

        btns = tk.Frame(self, bg=theme["bg"])
        btns.pack(fill="x", padx=16, pady=12)
        tk.Button(btns, text="Copy Report", bg=theme["card_bg"], fg=theme["text_primary"], bd=0, command=self._copy).pack(side="left")
        tk.Button(btns, text="Close", bg=theme["accent"], fg="white", bd=0, padx=20, command=self.destroy).pack(side="right")

        self._log = log_text
        self._findings = findings

    def _copy(self):
        self.clipboard_clear()
        report = "\n".join([f"{f['title']}: {f['description']} Fix: {f['fix']}" for f in self._findings]) + "\n\nLog:\n" + self._log[-2000:]
        self.clipboard_append(report)


class ConfirmDialog(tk.Toplevel):
    def __init__(self, parent, theme, title, message, on_confirm: Callable, danger=False):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=theme["bg"])
        self.geometry("420x180")
        self.transient(parent)
        self.grab_set()
        tk.Label(self, text=title, font=("Segoe UI", 12, "bold"), bg=theme["bg"], fg=theme["error"] if danger else theme["text_primary"]).pack(pady=(20, 6))
        tk.Label(self, text=message, font=("Segoe UI", 9), bg=theme["bg"], fg=theme["text_secondary"], wraplength=380, justify="left").pack(padx=20, pady=4)
        btns = tk.Frame(self, bg=theme["bg"])
        btns.pack(side="bottom", fill="x", padx=20, pady=16)
        tk.Button(btns, text="Cancel", bg=theme["card_bg"], fg=theme["text_secondary"], bd=0, padx=16, command=self.destroy).pack(side="right", padx=4)
        tk.Button(btns, text="Confirm", bg=theme["error"] if danger else theme["accent"], fg="white", bd=0, padx=16, command=lambda: (on_confirm(), self.destroy())).pack(side="right", padx=4)


class FileExplorerDialog(tk.Toplevel):
    def __init__(self, parent, theme, mc_dir, on_select=None):
        super().__init__(parent)
        self.title(f"File Explorer • {mc_dir}")
        self.configure(bg=theme["bg"])
        self.geometry("780x520")
        self.transient(parent)

        from omnilauncher.services.file_explorer import list_files, get_bookmarks

        self.mc_dir = mc_dir
        self.current_path = mc_dir
        self.on_select = on_select
        self.theme = theme

        left = tk.Frame(self, bg=theme["sidebar_bg"], width=180)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Label(left, text="Bookmarks", font=("Segoe UI", 10, "bold"), bg=theme["sidebar_bg"], fg=theme["text_primary"]).pack(anchor="w", padx=12, pady=(12, 6))

        self.bm_frame = tk.Frame(left, bg=theme["sidebar_bg"])
        self.bm_frame.pack(fill="x")

        def open_bm(path):
            self.current_path = path
            self._refresh()

        for bm in get_bookmarks(mc_dir):
            b = tk.Button(self.bm_frame, text=f"{bm['icon']}  {bm['name']}", anchor="w", bg=theme["sidebar_bg"], fg=theme["text_secondary"] if bm["exists"] else theme["text_muted"], bd=0, font=("Segoe UI", 9), command=lambda p=bm["path"]: open_bm(p))
            b.pack(fill="x", padx=6, pady=2)

        right = tk.Frame(self, bg=theme["bg"])
        right.pack(side="right", fill="both", expand=True)

        toolbar = tk.Frame(right, bg=theme["header_bg"], height=40)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)
        self.path_label = tk.Label(toolbar, text=mc_dir, font=("Segoe UI", 9), bg=theme["header_bg"], fg=theme["text_secondary"])
        self.path_label.pack(side="left", padx=12)
        tk.Button(toolbar, text="↑ Up", bg=theme["card_bg"], fg=theme["text_secondary"], bd=0, font=("Segoe UI", 8), command=self._go_up).pack(side="right", padx=8, pady=6)

        self.listbox = tk.Listbox(right, bg=theme["input_bg"], fg=theme["text_primary"], bd=0, font=("Segoe UI", 10), selectbackground=theme["sidebar_active"])
        self.listbox.pack(fill="both", expand=True, padx=12, pady=8)
        self.listbox.bind("<Double-Button-1>", lambda e: self._open_selected())

        btns = tk.Frame(right, bg=theme["bg"])
        btns.pack(fill="x", padx=12, pady=8)
        tk.Button(btns, text="Open Folder", bg=theme["card_bg"], fg=theme["text_secondary"], bd=0, command=lambda: __import__("webbrowser").open(self.current_path) if False else self._open_os()).pack(side="left")
        tk.Button(btns, text="Close", bg=theme["accent"], fg="white", bd=0, command=self.destroy).pack(side="right")

        self._refresh()

    def _refresh(self):
        from omnilauncher.services.file_explorer import list_files

        self.path_label.configure(text=self.current_path)
        self.listbox.delete(0, "end")
        items = list_files(self.current_path)
        self._items = items
        for it in items:
            prefix = "📁" if it["is_dir"] else "📄"
            self.listbox.insert("end", f"{prefix}  {it['name']}  ({it['size']} bytes)" if not it["is_dir"] else f"{prefix}  {it['name']}/")

    def _open_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        it = self._items[idx]
        if it["is_dir"]:
            self.current_path = it["path"]
            self._refresh()
        else:
            if self.on_select:
                self.on_select(it["path"])

    def _go_up(self):
        import os
        from pathlib import Path

        parent = str(Path(self.current_path).parent)
        if parent and len(parent) >= len(self.mc_dir) - 10:  # prevent going too far but allow
            self.current_path = parent
            self._refresh()
        else:
            self.current_path = self.mc_dir
            self._refresh()

    def _open_os(self):
        try:
            import os, platform, subprocess

            p = self.current_path
            if platform.system() == "Windows":
                os.startfile(p)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", p])
            else:
                subprocess.Popen(["xdg-open", p])
        except Exception:
            pass
