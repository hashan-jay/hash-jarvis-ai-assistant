"""CustomTkinter chat UI for HASH-JARVIS."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

import config
from backend.chat_service import ChatService
from gui import theme


class HashJarvisApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode(config.APPEARANCE_MODE)
        ctk.set_default_color_theme(str(theme.THEME_PATH))

        self.title(config.APP_TITLE)
        self.geometry(config.APP_GEOMETRY)
        self.minsize(960, 640)
        self.configure(fg_color=theme.BG)

        self.service = ChatService()
        self._busy = False
        self._assistant_bubble: Optional[ctk.CTkTextbox] = None

        self._build_layout()
        self.refresh_status()

    def _section_label(self, parent: ctk.CTkFrame, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text.upper(),
            anchor="w",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=theme.SECTION,
        ).pack(padx=18, pady=(16, 4), fill="x")

    def _ghost_button(self, parent, text: str, command) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color="transparent",
            hover_color=theme.ACCENT_GLOW,
            border_width=1,
            border_color=theme.BORDER_SOFT,
            text_color=theme.TEXT_SOFT,
        )

    def _build_layout(self) -> None:
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Accent rail
        self.accent_rail = ctk.CTkFrame(
            self, width=3, corner_radius=0, fg_color=theme.ACCENT_DIM
        )
        self.accent_rail.grid(row=0, column=0, sticky="ns")
        self.accent_rail.grid_propagate(False)

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self, width=268, corner_radius=0, fg_color=theme.SIDEBAR
        )
        self.sidebar.grid(row=0, column=1, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=18, pady=(22, 8))

        ctk.CTkLabel(
            brand,
            text="◉  SYSTEM ONLINE",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color=theme.ONLINE,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand,
            text=config.ASSISTANT_NAME,
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=theme.ACCENT,
            anchor="w",
        ).pack(anchor="w", pady=(6, 0))

        ctk.CTkLabel(
            brand,
            text="Local · Offline · Private",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=theme.TAGLINE,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=theme.BORDER, corner_radius=0
        ).pack(fill="x", padx=18, pady=(12, 4))

        self.new_chat_btn = ctk.CTkButton(
            self.sidebar,
            text="▸  New Session",
            command=self.on_new_chat,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
        )
        self.new_chat_btn.pack(padx=18, pady=(10, 6), fill="x")

        self.refresh_btn = self._ghost_button(
            self.sidebar, "↻  Sync Models", self.refresh_status
        )
        self.refresh_btn.pack(padx=18, pady=4, fill="x")

        self._section_label(self.sidebar, "Neural Core")
        self.model_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["No models found"],
            command=self.on_model_change,
            height=34,
            fg_color=theme.SURFACE_RAISED,
            button_color=theme.SURFACE,
            button_hover_color=theme.ACCENT_DIM,
            dropdown_fg_color=theme.SURFACE_RAISED,
            dropdown_hover_color=theme.ACCENT_GLOW,
            text_color=theme.TEXT,
        )
        self.model_menu.pack(padx=18, pady=4, fill="x")

        self._section_label(self.sidebar, "Pull Model")
        self.pull_entry = ctk.CTkEntry(
            self.sidebar,
            placeholder_text="e.g. llama3.2:3b",
            height=34,
            border_color=theme.BORDER_SOFT,
            fg_color=theme.BG,
        )
        self.pull_entry.pack(padx=18, pady=4, fill="x")
        self.pull_entry.insert(0, config.DEFAULT_MODEL)

        self.pull_btn = ctk.CTkButton(
            self.sidebar,
            text="↓  Download Model",
            command=self.on_pull_model,
            height=34,
        )
        self.pull_btn.pack(padx=18, pady=6, fill="x")

        self._section_label(self.sidebar, "Memory Bus")
        self.memory_switch = ctk.CTkSwitch(
            self.sidebar,
            text="ChromaDB Memory",
            command=self.on_toggle_memory,
            font=ctk.CTkFont(size=12),
            text_color=theme.TEXT_SOFT,
            progress_color=theme.ACCENT_DIM,
            button_color=theme.TEXT,
            button_hover_color=theme.ACCENT,
        )
        self.memory_switch.pack(padx=18, pady=(4, 8), anchor="w")
        if config.ENABLE_MEMORY_BY_DEFAULT:
            self.memory_switch.select()

        self.clear_memory_btn = self._ghost_button(
            self.sidebar, "Clear Memory", self.on_clear_memory
        )
        self.clear_memory_btn.pack(padx=18, pady=4, fill="x")

        status_wrap = ctk.CTkFrame(
            self.sidebar,
            fg_color=theme.SURFACE,
            border_width=1,
            border_color=theme.BORDER,
            corner_radius=8,
        )
        status_wrap.pack(padx=18, pady=(20, 18), fill="x", side="bottom")

        ctk.CTkLabel(
            status_wrap,
            text="STATUS",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(padx=12, pady=(10, 2), fill="x")

        self.status_label = ctk.CTkLabel(
            status_wrap,
            text="Checking Ollama...",
            wraplength=210,
            justify="left",
            anchor="w",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=theme.TEXT_SOFT,
        )
        self.status_label.pack(padx=12, pady=(0, 12), fill="x")

        # Main chat area
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color=theme.MAIN)
        self.main.grid(row=0, column=2, sticky="nsew")
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        # Top HUD bar
        self.topbar = ctk.CTkFrame(
            self.main, height=52, corner_radius=0, fg_color=theme.SURFACE
        )
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.grid_propagate(False)
        self.topbar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.topbar,
            text="SECURE CHANNEL  ·  LOCAL INFERENCE",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=22, pady=14)

        self.hud_chip = ctk.CTkLabel(
            self.topbar,
            text="  STANDBY  ",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=theme.ACCENT,
            fg_color=theme.ACCENT_GLOW,
            corner_radius=4,
            height=26,
        )
        self.hud_chip.grid(row=0, column=1, sticky="e", padx=22, pady=14)

        ctk.CTkFrame(
            self.main, height=1, fg_color=theme.BORDER, corner_radius=0
        ).grid(row=0, column=0, sticky="sew")

        self.chat_frame = ctk.CTkScrollableFrame(
            self.main,
            fg_color=theme.MAIN,
            scrollbar_button_color=theme.BORDER_SOFT,
            scrollbar_button_hover_color=theme.ACCENT_DIM,
        )
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(14, 8))
        self.chat_frame.grid_columnconfigure(0, weight=1)

        self.composer = ctk.CTkFrame(
            self.main,
            fg_color=theme.COMPOSER,
            border_width=1,
            border_color=theme.BORDER,
            corner_radius=12,
        )
        self.composer.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 18))
        self.composer.grid_columnconfigure(0, weight=1)

        self.input_box = ctk.CTkTextbox(
            self.composer,
            height=92,
            fg_color=theme.BG,
            border_width=1,
            border_color=theme.BORDER_SOFT,
            text_color=theme.TEXT,
            font=ctk.CTkFont(size=14),
        )
        self.input_box.grid(row=0, column=0, sticky="ew", padx=(12, 8), pady=12)
        self.input_box.bind("<Control-Return>", self._on_ctrl_enter)

        self.send_btn = ctk.CTkButton(
            self.composer,
            text="Transmit\nCtrl+Enter",
            width=118,
            height=92,
            command=self.on_send,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
        )
        self.send_btn.grid(row=0, column=1, padx=(0, 12), pady=12)

        self._add_system_note(
            f"Good day. {config.ASSISTANT_NAME} is online and running locally.\n"
            "1) Ensure Ollama is running\n"
            "2) Select or download a model from the sidebar\n"
            "3) Ask anything — Ctrl+Enter to send\n"
            "How may I assist you?"
        )

    def _on_ctrl_enter(self, _event=None):
        self.on_send()
        return "break"

    def _add_system_note(self, text: str) -> None:
        wrap = ctk.CTkFrame(
            self.chat_frame,
            fg_color=theme.SURFACE,
            border_width=1,
            border_color=theme.BORDER,
            corner_radius=8,
        )
        wrap.grid(sticky="ew", pady=(0, 14))

        ctk.CTkLabel(
            wrap,
            text="// SYSTEM",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color=theme.ACCENT_DIM,
            anchor="w",
        ).pack(padx=14, pady=(10, 2), anchor="w")

        note = ctk.CTkLabel(
            wrap,
            text=text,
            justify="left",
            anchor="w",
            wraplength=720,
            font=ctk.CTkFont(size=13),
            text_color=theme.SYSTEM_NOTE,
        )
        note.pack(padx=14, pady=(0, 12), anchor="w")

    def _add_bubble(self, role: str, text: str = "") -> ctk.CTkTextbox:
        is_user = role == "user"
        outer = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        outer.grid(sticky="ew", pady=8)
        outer.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            outer,
            text="YOU" if is_user else config.ASSISTANT_NAME,
            anchor="e" if is_user else "w",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=theme.USER_LABEL if is_user else theme.ASSISTANT_LABEL,
        )
        label.grid(row=0, column=0, sticky="e" if is_user else "w", padx=6, pady=(0, 2))

        bubble = ctk.CTkTextbox(
            outer,
            height=40,
            wrap="word",
            activate_scrollbars=False,
            fg_color=theme.USER_BUBBLE if is_user else theme.ASSISTANT_BUBBLE,
            border_width=1,
            border_color=theme.ACCENT_GLOW if is_user else theme.BORDER,
            text_color=theme.TEXT,
            font=ctk.CTkFont(size=14),
            corner_radius=10,
        )
        bubble.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(90, 0) if is_user else (0, 90),
        )
        bubble.insert("1.0", text)
        bubble.configure(state="disabled")
        self._autosize_bubble(bubble)
        self.after(50, self._scroll_to_bottom)
        return bubble

    def _autosize_bubble(self, bubble: ctk.CTkTextbox) -> None:
        content = bubble.get("1.0", "end-1c")
        lines = max(content.count("\n") + 1, 1)
        approx = min(max(lines * 22, 48), 360)
        bubble.configure(height=approx)

    def _scroll_to_bottom(self) -> None:
        try:
            self.chat_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.send_btn.configure(state=state)
        self.pull_btn.configure(state=state)
        self.new_chat_btn.configure(state=state)
        self.refresh_btn.configure(state=state)
        self.hud_chip.configure(
            text="  PROCESSING  " if busy else "  READY  ",
            text_color=theme.WARN if busy else theme.ONLINE,
            fg_color="#3F2A14" if busy else "#0F2E24",
        )

    def refresh_status(self) -> None:
        status = self.service.status()
        models = status["models"] or ["No models found"]
        self.model_menu.configure(values=models)

        if status["models"]:
            selected = (
                self.service.model
                if self.service.model in status["models"]
                else status["models"][0]
            )
            self.service.set_model(selected)
            self.model_menu.set(selected)
        else:
            self.model_menu.set("No models found")

        if not status["ollama_available"]:
            text = "Ollama: OFFLINE\nStart the Ollama app\nor run `ollama serve`."
            if not self._busy:
                self.hud_chip.configure(
                    text="  OFFLINE  ",
                    text_color=theme.OFFLINE,
                    fg_color="#3F1D1D",
                )
        elif not status["models"]:
            text = "Ollama: ONLINE\nNo models yet —\npull one below."
            if not self._busy:
                self.hud_chip.configure(
                    text="  NO MODEL  ",
                    text_color=theme.WARN,
                    fg_color="#3F2A14",
                )
        else:
            memory = "ON" if status["memory_enabled"] else "OFF"
            text = (
                f"Ollama: ONLINE\n"
                f"Model: {self.service.model}\n"
                f"Memory: {memory}"
            )
            if status["memory_error"]:
                text += f"\nNote: {status['memory_error'][:80]}"
            if not self._busy:
                self.hud_chip.configure(
                    text="  READY  ",
                    text_color=theme.ONLINE,
                    fg_color="#0F2E24",
                )

        self.status_label.configure(text=text)

    def on_model_change(self, model: str) -> None:
        if model == "No models found":
            return
        self.service.set_model(model)
        self.refresh_status()

    def on_toggle_memory(self) -> None:
        enabled = bool(self.memory_switch.get())
        self.service.set_memory_enabled(enabled)
        self.refresh_status()

    def on_clear_memory(self) -> None:
        if messagebox.askyesno("Clear memory", "Delete all stored conversation memories?"):
            self.service.clear_memory()
            self._add_system_note("Memory cleared.")
            self.refresh_status()

    def on_new_chat(self) -> None:
        if self._busy:
            return
        self.service.new_chat()
        for child in self.chat_frame.winfo_children():
            child.destroy()
        self._add_system_note("New session initiated. How may I help?")

    def on_send(self) -> None:
        if self._busy:
            return
        text = self.input_box.get("1.0", "end-1c").strip()
        if not text:
            return

        self.input_box.delete("1.0", "end")
        self._add_bubble("user", text)
        self._assistant_bubble = self._add_bubble("assistant", "")
        self._set_busy(True)

        thread = threading.Thread(target=self._generate, args=(text,), daemon=True)
        thread.start()

    def _generate(self, text: str) -> None:
        collected: list[str] = []
        try:
            for token in self.service.stream_reply(text):
                collected.append(token)
                snapshot = "".join(collected)
                self.after(0, self._update_assistant_bubble, snapshot)
            self.after(0, self.refresh_status)
        except Exception as exc:
            message = str(exc)
            self.after(0, self._update_assistant_bubble, f"Error: {message}")
        finally:
            self.after(0, self._set_busy, False)

    def _update_assistant_bubble(self, text: str) -> None:
        if self._assistant_bubble is None:
            return
        bubble = self._assistant_bubble
        bubble.configure(state="normal")
        bubble.delete("1.0", "end")
        bubble.insert("1.0", text)
        bubble.configure(state="disabled")
        self._autosize_bubble(bubble)
        self._scroll_to_bottom()

    def on_pull_model(self) -> None:
        if self._busy:
            return
        model = self.pull_entry.get().strip()
        if not model:
            messagebox.showwarning("Pull model", "Enter a model name first.")
            return

        self._set_busy(True)
        self.status_label.configure(text=f"Downloading {model}...\nThis may take a while.")
        thread = threading.Thread(target=self._pull_model, args=(model,), daemon=True)
        thread.start()

    def _pull_model(self, model: str) -> None:
        try:
            last_status = "starting"
            for event in self.service.pull_model(model):
                status = event.get("status", "pulling")
                completed = event.get("completed")
                total = event.get("total")
                if completed and total:
                    pct = int((completed / total) * 100)
                    last_status = f"{status} ({pct}%)"
                else:
                    last_status = str(status)
                self.after(0, self.status_label.configure, {"text": f"{model}\n{last_status}"})

            self.service.set_model(model)
            self.after(0, self.refresh_status)
            self.after(
                0,
                self._add_system_note,
                f"Model ready: {model}. At your service.",
            )
        except Exception as exc:
            self.after(
                0,
                lambda: messagebox.showerror("Pull failed", str(exc)),
            )
            self.after(0, self.refresh_status)
        finally:
            self.after(0, self._set_busy, False)


def run_app() -> None:
    app = HashJarvisApp()
    app.mainloop()
