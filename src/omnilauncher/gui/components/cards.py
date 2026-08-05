"""Reusable cards - Instances, Accounts, Settings rows."""

import tkinter as tk
from typing import Dict, Callable
from datetime import datetime


ICON_COLORS = {
    "grass": "#5aad5a",
    "crafting_table": "#c49a6c",
    "furnace": "#7a7a7a",
    "diamond": "#5ec4d6",
    "emerald": "#2ecc71",
    "command_block": "#d67d2b",
    "bedrock": "#2b2b2b",
    "tnt": "#ff3b30",
    "chest": "#d3a56a",
    "book": "#c0392b",
    "anvil": "#444",
    "beacon": "#7dd6ff",
    "bricks": "#b04a3a",
    "dirt": "#866043",
    "stone": "#9b9b9b",
    "gold": "#ffcc00",
    "iron": "#d8d8d8",
    "redstone": "#ff0000",
    "lapis": "#2043c0",
    "nether": "#5a1a1a",
    "end": "#e6e3a8",
}


def _icon_color(name: str) -> str:
    return ICON_COLORS.get(name, "#e94560")


class InstanceCard(tk.Frame):
    def __init__(
        self,
        parent,
        instance: Dict,
        theme: Dict[str, str],
        on_play: Callable[[str], None],
        on_select: Callable[[str], None],
        on_context: Callable[[str, int, int], None] | None = None,
    ):
        super().__init__(parent, bg=theme["card_bg"], bd=0, highlightthickness=1, highlightbackground=theme["card_border"])
        self.instance = instance
        self.theme = theme
        self.on_play = on_play
        self.on_select = on_select
        self.on_context = on_context
        self._build()

    def _build(self):
        th = self.theme
        inst = self.instance

        # hover
        self.bind("<Enter>", lambda e: self.configure(bg=th["card_hover"]))
        self.bind("<Leave>", lambda e: self.configure(bg=th["card_bg"]))

        inner = tk.Frame(self, bg=th["card_bg"])
        inner.pack(fill="both", expand=True, padx=12, pady=10)
        inner.bind("<Enter>", lambda e: self._set_inner_bg(th["card_hover"], inner))
        inner.bind("<Leave>", lambda e: self._set_inner_bg(th["card_bg"], inner))
        inner.bind("<Button-1>", lambda e: self.on_select(inst["id"]))
        if self.on_context:
            inner.bind("<Button-3>", lambda e: self.on_context(inst["id"], e.x_root, e.y_root))

        # icon
        icon_frame = tk.Frame(inner, bg=th["card_bg"], width=48, height=48)
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        c = tk.Canvas(icon_frame, width=48, height=48, bg=th["card_bg"], highlightthickness=0)
        c.pack()
        color = _icon_color(inst.get("icon", "grass"))
        c.create_rectangle(4, 4, 44, 44, fill=color, outline="", width=0)
        # pixel art hint - darker top
        c.create_rectangle(4, 4, 44, 14, fill="#ffffff", outline="", stipple="gray25")
        # letter
        letter = inst.get("name", "?")[:1].upper()
        c.create_text(24, 26, text=letter, font=("Segoe UI", 14, "bold"), fill="white")
        # fav star
        if inst.get("favorite"):
            c.create_text(38, 8, text="★", font=("Segoe UI", 10), fill="#ffcc00")

        # text
        txt = tk.Frame(inner, bg=th["card_bg"])
        txt.pack(side="left", fill="both", expand=True, padx=12)
        txt.bind("<Button-1>", lambda e: self.on_select(inst["id"]))

        name_lbl = tk.Label(
            txt,
            text=inst.get("name", "Unnamed"),
            font=("Segoe UI", 10, "bold"),
            bg=th["card_bg"],
            fg=th["text_primary"],
            anchor="w",
        )
        name_lbl.pack(anchor="w", fill="x")
        name_lbl.bind("<Button-1>", lambda e: self.on_select(inst["id"]))

        ver = inst.get("version") or "No version"
        loader = inst.get("loader", "vanilla")
        details = f"{ver} • {loader} • {inst.get('group','Custom')}"
        detail_lbl = tk.Label(
            txt,
            text=details,
            font=("Segoe UI", 8),
            bg=th["card_bg"],
            fg=th["text_secondary"],
            anchor="w",
        )
        detail_lbl.pack(anchor="w")

        # playtime
        pt = inst.get("playtime_minutes", 0)
        last = inst.get("last_played", "")
        if last:
            try:
                dt = datetime.fromisoformat(last)
                last_s = dt.strftime("%b %d")
            except Exception:
                last_s = last[:10]
            meta = f"Played {last_s}"
            if pt:
                meta += f" • {pt//60}h {pt%60}m"
        else:
            meta = "Never played" if not pt else f"{pt//60}h {pt%60}m"
        meta_lbl = tk.Label(
            txt,
            text=meta,
            font=("Segoe UI", 7),
            bg=th["card_bg"],
            fg=th["text_muted"],
            anchor="w",
        )
        meta_lbl.pack(anchor="w")

        # play button
        play_btn = tk.Button(
            inner,
            text="▶",
            font=("Segoe UI", 10, "bold"),
            bg=th["accent"],
            fg="white",
            activebackground=th["accent_hover"],
            bd=0,
            padx=12,
            pady=4,
            command=lambda: self.on_play(inst["id"]),
        )
        play_btn.pack(side="right")

    def _set_inner_bg(self, bg, frame):
        try:
            self.configure(bg=bg)
            frame.configure(bg=bg)
            for c in frame.winfo_children():
                if isinstance(c, tk.Frame):
                    c.configure(bg=bg)
                    for cc in c.winfo_children():
                        if isinstance(cc, (tk.Frame, tk.Label)):
                            try:
                                cc.configure(bg=bg)
                            except Exception:
                                pass
                        if isinstance(cc, tk.Canvas):
                            cc.configure(bg=bg)
                elif isinstance(c, tk.Label):
                    c.configure(bg=bg)
        except Exception:
            pass


class AccountCard(tk.Frame):
    def __init__(
        self,
        parent,
        account: Dict,
        theme: Dict[str, str],
        index: int,
        selected: bool,
        on_select: Callable[[int], None],
        on_delete: Callable[[str], None],
    ):
        super().__init__(parent, bg=theme["card_bg"], highlightthickness=1, highlightbackground=theme["card_border"])
        self.theme = theme
        self.account = account
        th = theme
        inner = tk.Frame(self, bg=th["card_bg"])
        inner.pack(fill="x", padx=12, pady=10)

        # avatar
        av = tk.Canvas(inner, width=48, height=48, bg=th["card_bg"], highlightthickness=0)
        av.pack(side="left")
        # skin type affects shape - Steve wider shoulders?
        skin_color = "#e8c4a8"
        shirt_color = th["accent"]
        if account.get("skin_type") == "alex":
            shirt_color = th["accent_secondary"]
        av.create_rectangle(8, 4, 40, 24, fill=skin_color, outline="")
        av.create_rectangle(12, 24, 36, 40, fill=shirt_color, outline="")
        av.create_rectangle(4, 24, 12, 38, fill=skin_color, outline="")
        av.create_rectangle(36, 24, 44, 38, fill=skin_color, outline="")

        txt = tk.Frame(inner, bg=th["card_bg"])
        txt.pack(side="left", padx=12, fill="x", expand=True)

        tk.Label(
            txt,
            text=account.get("username", "Steve"),
            font=("Segoe UI", 11, "bold"),
            bg=th["card_bg"],
            fg=th["text_primary"],
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            txt,
            text=f'{account.get("type","offline")} • {account.get("skin_type","steve")} • {account.get("uuid","")[:8]}',
            font=("Segoe UI", 8),
            bg=th["card_bg"],
            fg=th["text_secondary"],
            anchor="w",
        ).pack(anchor="w")

        if selected:
            tk.Label(
                inner,
                text="● SELECTED",
                font=("Segoe UI", 8, "bold"),
                bg=th["card_bg"],
                fg=th["success"],
            ).pack(side="left", padx=8)

        # buttons
        btn_frame = tk.Frame(inner, bg=th["card_bg"])
        btn_frame.pack(side="right")

        if not selected:
            tk.Button(
                btn_frame,
                text="Select",
                font=("Segoe UI", 8, "bold"),
                bg=th["accent"],
                fg="white",
                bd=0,
                command=lambda: on_select(index),
            ).pack(side="left", padx=4)

        if len(parent.winfo_children()) > 1 or True:
            tk.Button(
                btn_frame,
                text="✕",
                font=("Segoe UI", 8),
                bg=th["card_bg"],
                fg=th["text_muted"],
                bd=0,
                command=lambda: on_delete(account.get("uuid", "")),
            ).pack(side="left", padx=4)


class SettingsRow(tk.Frame):
    """A row with label + control + description for settings."""

    def __init__(self, parent, title: str, description: str, theme: Dict[str, str], control: tk.Widget | None = None):
        super().__init__(parent, bg=theme["card_bg"])
        self.theme = theme
        left = tk.Frame(self, bg=theme["card_bg"])
        left.pack(side="left", fill="x", expand=True, padx=16, pady=12)

        tk.Label(
            left,
            text=title,
            font=("Segoe UI", 10, "bold"),
            bg=theme["card_bg"],
            fg=theme["text_primary"],
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            left,
            text=description,
            font=("Segoe UI", 8),
            bg=theme["card_bg"],
            fg=theme["text_secondary"],
            wraplength=420,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        if control is not None:
            right = tk.Frame(self, bg=theme["card_bg"])
            right.pack(side="right", padx=16)
            control.pack(in_=right)
            # reparent control's bg if possible
            try:
                control.configure(bg=theme["input_bg"])
            except Exception:
                pass

        # separator
        sep = tk.Frame(parent, bg=theme["separator"], height=1)
        sep.pack(fill="x", padx=16)
