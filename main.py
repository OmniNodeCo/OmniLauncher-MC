import shutil
import tkinter
from tkinter import ttk
from tkinter.messagebox import askquestion

from launcher import get_latest_version, get_release_versions, launch

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
        root.destroy()
    else:
        pass

def open_changelog():
    TopLevelWindow = tkinter.Toplevel()
    TopLevelWindow.title("Changelog")
    TopLevelWindow.geometry("500x400")
    text_box = tkinter.Text(TopLevelWindow, wrap="word")
    text_box.pack(fill="both", expand=True)
    with open("Changelog.txt", "r", encoding="utf-8") as file:
        content = file.read()
        text_box.insert("1.0", content)
        text_box.config(state="disabled")


def open_terms():
    TopLevelWindow = tkinter.Toplevel()
    TopLevelWindow.title("Terms")
    TopLevelWindow.geometry("500x400")
    text_box = tkinter.Text(TopLevelWindow, wrap="word")
    text_box.pack(fill="both", expand=True)
    with open("TERMS.txt", "r", encoding="utf-8") as file:
        content = file.read()
        text_box.insert("1.0", content)
        text_box.config(state="disabled")


def open_license():
    TopLevelWindow = tkinter.Toplevel()
    TopLevelWindow.title("License")
    TopLevelWindow.geometry("500x400")
    text_box = tkinter.Text(TopLevelWindow, wrap="word")
    text_box.pack(fill="both", expand=True)
    with open("LICENSE.txt", "r", encoding="utf-8") as file:
        content = file.read()
        text_box.insert("1.0", content)
        text_box.config(state="disabled")

def delalldata():
    answer = askquestion("Are you sure you want to delete all data?")
    if answer == "yes":
        shutil.rmtree("%AppData%/.minecraft")
    else:
        pass


#Launcher Tab config
tkinter.Button(Launcher_tab, text="Launch", command=launch).grid(row=4, column=0)
tkinter.Button(Launcher_tab, text="Quit", command=ask_quit).grid(row=5, column=0)

#About Tab Config
tkinter.Button(About_tab, text="Open Changelog", command=open_changelog).grid(row=5, column=0)
tkinter.Button(About_tab, text="Open Terms", command=open_terms).grid(row=6, column=0)
tkinter.Button(About_tab, text="Open License", command=open_license).grid(row=7, column=0)

#Settings Tab Config
tkinter.Button(Settings_tab, text="Delete ALL Data", bg="red", command=delalldata).grid(row=1, column=5)

#Combobox
selected_version = tkinter.StringVar()

version_combobox = ttk.Combobox(
    Launcher_tab,
    textvariable=selected_version,
    values=get_release_versions(),
    state="readonly"
)

version_combobox.set(get_latest_version())
version_combobox.grid(row=6, column=0)


#Loop
root.mainloop()