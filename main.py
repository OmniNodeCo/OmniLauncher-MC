#-------IMPORTS-------#

import tkinter
import json
import os
import shutil
from tkinter import ttk
from tkinter.messagebox import askquestion
import minecraft_launcher_lib
import tkinter.messagebox
from scripts.launcher import get_latest_version, get_release_versions, launch


#------ROOT------#
root = tkinter.Tk()
root.title("OmniLauncher-MC")
root.geometry("500x500")

#NoteBook Setup
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

#Tabs Setup
Launcher_tab = ttk.Frame(notebook)
About_tab = ttk.Frame(notebook)
Settings_tab = ttk.Frame(notebook)

#Tabs Name
notebook.add(Launcher_tab, text="Launcher")
notebook.add(About_tab, text="About")
notebook.add(Settings_tab, text="Settings")


#Functions
def ask_quit():
    answer = askquestion("Message from OmniLauncher", "Are you sure you want to quit?")
    if answer == "yes":
        on_closing()
    else:
        pass

def open_text_file(title, filename):
    TopLevelWindow = tkinter.Toplevel()
    TopLevelWindow.title(title)
    TopLevelWindow.geometry("500x400")
    text_box = tkinter.Text(TopLevelWindow, wrap="word")
    text_box.pack(fill="both", expand=True)
    with open(filename, "r", encoding="utf-8") as file:
        content = file.read()
        text_box.insert("1.0", content)
        text_box.config(state="disabled")

def delalldata():
    answer = askquestion("Warning", "Are you sure you want to delete all data?")
    if answer == "yes":
        shutil.rmtree(minecraft_launcher_lib.utils.get_minecraft_directory())
    else:
        pass

def load_settings():
    if os.path.exists("settings.json"):
        with open("settings.json", "r") as file:
            return json.load(file)
    else:
        return {
            "username": "Steve",
            "ram": 4,
            "java_path": "",
            "last_version": ""
        }

def save_settings():
    settings = {
        "username": username_entry.get(),
        "ram": ram_slider.get(),
        "java_path": java_entry.get(),
        "last_version": version_combobox.get()
    }
    with open("settings.json", "w") as file:
        json.dump(settings, file, indent=4)

def on_launch_clicked():
    username = username_entry.get()
    version = selected_version.get()
    ram = ram_slider.get()
    launch(username, version, ram)

def refresh_error_log():
    error_log_text.config(state="normal")
    error_log_text.delete("1.0", "end")
    if os.path.exists("launcher.log"):
        with open("launcher.log", "r") as file:
            content = file.read()
            error_log_text.insert("1.0", content)
    else:
        error_log_text.insert("1.0", "No errors logged.")
    error_log_text.config(state="disabled")

def copy_error_log():
    content = error_log_text.get("1.0", "end")
    root.clipboard_clear()
    root.clipboard_append(content)
    tkinter.messagebox.showinfo("Copied", "Error log copied to clipboard.")

def clear_error_log():
    answer = askquestion("Warning", "Clear all error logs?")
    if answer == "yes":
        with open("launcher.log", "w") as file:
            file.write("")
        refresh_error_log()

def on_tab_changed(event):
    if notebook.index("current") == 2:
        refresh_error_log()

def on_closing():
    save_settings()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

username_entry = tkinter.StringVar()
settings = load_settings()
username_entry.set(settings["username"])

#Launcher Tab Config
tkinter.Button(Launcher_tab, text="Launch", command=on_launch_clicked).grid(row=0, column=0, padx=10, pady=5)
tkinter.Button(Launcher_tab, text="Quit", command=ask_quit).grid(row=1, column=0, padx=10, pady=5)

#UserName Entry
tkinter.Label(Launcher_tab, text="UserName").grid(row=2, column=0, padx=10, pady=5)
tkinter.Entry(Launcher_tab, textvariable=username_entry).grid(row=3, column=0, padx=10, pady=5)

#Combobox
selected_version = tkinter.StringVar()
version_combobox = ttk.Combobox(
    Launcher_tab,
    textvariable=selected_version,
    values=get_release_versions(),
    state="readonly"
)
version_combobox.set(get_latest_version())
version_combobox.grid(row=4, column=0, padx=10, pady=5)

#About Tab Config
tkinter.Button(About_tab, text="Open Changelog", command=lambda:open_text_file("Changelog", "Changelog.txt")).grid(row=0, column=0, padx=10, pady=5)
tkinter.Button(About_tab, text="Open Terms", command=lambda:open_text_file("Terms", "TERMS.txt")).grid(row=1, column=0, padx=10, pady=5)
tkinter.Button(About_tab, text="Open License", command=lambda:open_text_file("License", "LICENSE.txt")).grid(row=2, column=0, padx=10, pady=5)

#Settings Tab Config
tkinter.Label(Settings_tab, text="RAM (GB)").grid(row=0, column=0, padx=10, pady=5)
ram_slider = tkinter.Scale(Settings_tab, from_=1, to=16, orient="horizontal")
ram_slider.set(settings["ram"])
ram_slider.grid(row=0, column=1, padx=10, pady=5)

tkinter.Label(Settings_tab, text="Java Path").grid(row=1, column=0, padx=10, pady=5)
java_entry = tkinter.Entry(Settings_tab)
java_entry.grid(row=1, column=1, padx=10, pady=5)
java_entry.insert(0, settings["java_path"])

tkinter.Button(Settings_tab, text="Delete ALL Data", bg="red", command=delalldata).grid(row=2, column=0, padx=10, pady=5)

#Error Log Section
tkinter.Label(Settings_tab, text="Error Log").grid(row=3, column=0, padx=10, pady=5)
error_log_text = tkinter.Text(Settings_tab, height=10, width=40, wrap="word")
error_log_text.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
error_log_text.config(state="disabled")

tkinter.Button(Settings_tab, text="Refresh", command=refresh_error_log).grid(row=5, column=0, sticky="e", padx=5)
tkinter.Button(Settings_tab, text="Copy", command=copy_error_log).grid(row=5, column=1, sticky="w", padx=5)
tkinter.Button(Settings_tab, text="Clear Log", command=clear_error_log).grid(row=5, column=2, sticky="w", padx=5)

#Loop
root.mainloop()