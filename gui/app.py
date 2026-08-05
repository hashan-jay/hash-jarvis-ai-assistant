"""CustomTkinter chat UI for ZYNTAKSgenAI."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

import config
from backend.chat_service import ChatService
from gui import theme
from gui.fonts import load_app_fonts


class HashJarvisApp(ctk.CTk):
    def __init__(self) -> None:
        self.brand_font_family = load_app_fonts()

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
            text=text,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=theme.SECTION,
        ).pack(padx=18, pady=(18, 6), fill="x")

    def _ghost_button(self, parent, text: str, command) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color=theme.SURFACE_RAISED,
            hover_color="#1C1C1C",
            border_width=1,
            border_color="#3F5F66",
            text_color=theme.TEXT,
            corner_radius=999,
            height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
        )

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self, width=300, corner_radius=0, fg_color=theme.SIDEBAR
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(26, 10))

        ctk.CTkLabel(
            brand,
            text="• Innovation studio · Local AI",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED,
            anchor="w",
            fg_color=theme.SURFACE_RAISED,
            corner_radius=999,
            height=24,
        ).pack(anchor="w", ipadx=10)

        ctk.CTkLabel(
            brand,
            text=config.ASSISTANT_NAME,
            font=ctk.CTkFont(family=self.brand_font_family, size=22, weight="bold"),
            text_color=theme.ACCENT,
            anchor="w",
        ).pack(anchor="w", pady=(12, 0))

        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=theme.BORDER, corner_radius=0
        ).pack(fill="x", padx=20, pady=(16, 6))

        self.new_chat_btn = ctk.CTkButton(
            self.sidebar,
            text="New session →",
            command=self.on_new_chat,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            corner_radius=999,
        )
        self.new_chat_btn.pack(padx=20, pady=(12, 8), fill="x")

        self.refresh_btn = self._ghost_button(
            self.sidebar, "Sync models", self.refresh_status
        )
        self.refresh_btn.pack(padx=20, pady=4, fill="x")

        self._section_label(self.sidebar, "Model")
        self.model_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["No models found"],
            command=self.on_model_change,
            height=34,
            corner_radius=10,
            fg_color=theme.SURFACE_RAISED,
            button_color="#1C1C1C",
            button_hover_color=theme.ACCENT,
            dropdown_fg_color=theme.SURFACE_RAISED,
            dropdown_hover_color="#1C1C1C",
            text_color=theme.TEXT,
        )
        self.model_menu.pack(padx=20, pady=4, fill="x")

        self._section_label(self.sidebar, "Pull model")
        self.pull_entry = ctk.CTkEntry(
            self.sidebar,
            placeholder_text="e.g. llama3.2:3b",
            height=34,
            border_color=theme.BORDER,
            fg_color=theme.BG,
            corner_radius=10,
        )
        self.pull_entry.pack(padx=20, pady=4, fill="x")
        self.pull_entry.insert(0, config.DEFAULT_MODEL)

        self.pull_btn = ctk.CTkButton(
            self.sidebar,
            text="Download model →",
            command=self.on_pull_model,
            height=34,
            corner_radius=999,
        )
        self.pull_btn.pack(padx=20, pady=8, fill="x")

        self._section_label(self.sidebar, "Memory")
        self.memory_switch = ctk.CTkSwitch(
            self.sidebar,
            text="ChromaDB Memory",
            command=self.on_toggle_memory,
            font=ctk.CTkFont(size=12),
            text_color=theme.TEXT_SOFT,
            progress_color=theme.ACCENT,
            button_color=theme.TEXT,
            button_hover_color=theme.ACCENT_HOVER,
        )
        self.memory_switch.pack(padx=20, pady=(4, 8), anchor="w")
        if config.ENABLE_MEMORY_BY_DEFAULT:
            self.memory_switch.select()

        self.clear_memory_btn = self._ghost_button(
            self.sidebar, "Clear memory", self.on_clear_memory
        )
        self.clear_memory_btn.pack(padx=20, pady=4, fill="x")

        status_wrap = ctk.CTkFrame(
            self.sidebar,
            fg_color=theme.SURFACE_RAISED,
            border_width=1,
            border_color=theme.BORDER,
            corner_radius=16,
        )
        status_wrap.pack(padx=20, pady=(20, 20), fill="x", side="bottom")

        ctk.CTkLabel(
            status_wrap,
            text="Status",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(padx=14, pady=(12, 2), fill="x")

        self.status_label = ctk.CTkLabel(
            status_wrap,
            text="Checking Ollama...",
            wraplength=250,
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color=theme.TEXT_SOFT,
        )
        self.status_label.pack(padx=14, pady=(0, 14), fill="x")

        # Main chat area
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color=theme.MAIN)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        # Top bar
        self.topbar = ctk.CTkFrame(
            self.main, height=56, corner_radius=0, fg_color=theme.BG
        )
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.grid_propagate(False)
        self.topbar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.topbar,
            text="Local inference · Private by design",
            font=ctk.CTkFont(size=13),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=16)

        self.hud_chip = ctk.CTkLabel(
            self.topbar,
            text="  Ready  ",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=theme.TEXT_ON_ACCENT,
            fg_color=theme.ACCENT,
            corner_radius=999,
            height=28,
        )
        self.hud_chip.grid(row=0, column=1, sticky="e", padx=24, pady=14)

        ctk.CTkFrame(
            self.main, height=1, fg_color=theme.BORDER, corner_radius=0
        ).grid(row=0, column=0, sticky="sew")

        self.chat_frame = ctk.CTkScrollableFrame(
            self.main,
            fg_color=theme.MAIN,
            scrollbar_button_color=theme.BORDER_SOFT,
            scrollbar_button_hover_color=theme.ACCENT,
        )
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(16, 8))
        self.chat_frame.grid_columnconfigure(0, weight=1)

        self.composer = ctk.CTkFrame(
            self.main,
            fg_color=theme.SURFACE,
            border_width=1,
            border_color=theme.BORDER,
            corner_radius=16,
        )
        self.composer.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 20))
        self.composer.grid_columnconfigure(0, weight=1)

        self.input_box = ctk.CTkTextbox(
            self.composer,
            height=92,
            fg_color=theme.BG,
            border_width=1,
            border_color=theme.BORDER,
            text_color=theme.TEXT,
            font=ctk.CTkFont(size=14),
            corner_radius=12,
        )
        self.input_box.grid(row=0, column=0, sticky="ew", padx=(14, 10), pady=14)
        self.input_box.bind("<Control-Return>", self._on_ctrl_enter)

        self.send_btn = ctk.CTkButton(
            self.composer,
            text="Send →",
            width=110,
            height=92,
            command=self.on_send,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=999,
        )
        self.send_btn.grid(row=0, column=1, padx=(0, 14), pady=14)

        self._add_system_note(
            f"Welcome. {config.ASSISTANT_NAME} is online and running locally.\n"
            "1) Ensure Ollama is running\n"
            "2) Select or download a model from the sidebar\n"
            "3) Ask anything — Ctrl+Enter to send\n"
            "How may I help you build?"
        )

    def _on_ctrl_enter(self, _event=None):
        self.on_send()
        return "break"

    def _add_system_note(self, text: str) -> None:
        wrap = ctk.CTkFrame(
            self.chat_frame,
            fg_color="#0A0A0A",
            border_width=1,
            border_color=theme.BORDER,
            corner_radius=16,
        )
        wrap.grid(sticky="ew", pady=(0, 14))

        ctk.CTkLabel(
            wrap,
            text="System",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=theme.ACCENT,
            anchor="w",
        ).pack(padx=16, pady=(14, 2), anchor="w")

        note = ctk.CTkLabel(
            wrap,
            text=text,
            justify="left",
            anchor="w",
            wraplength=720,
            font=ctk.CTkFont(size=13),
            text_color=theme.SYSTEM_NOTE,
        )
        note.pack(padx=16, pady=(0, 14), anchor="w")

    def _add_bubble(self, role: str, text: str = "") -> ctk.CTkTextbox:
        is_user = role == "user"
        outer = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        outer.grid(sticky="ew", pady=8)
        outer.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            outer,
            text="You" if is_user else config.ASSISTANT_NAME,
            anchor="e" if is_user else "w",
            font=ctk.CTkFont(
                family=self.brand_font_family if not is_user else "Segoe UI",
                size=12 if not is_user else 11,
                weight="bold" if not is_user else "normal",
            ),
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
            border_color="#3F5F66" if is_user else theme.BORDER,
            text_color=theme.TEXT,
            font=ctk.CTkFont(size=14),
            corner_radius=16,
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
            text="  Processing  " if busy else "  Ready  ",
            text_color=theme.TEXT_ON_ACCENT if not busy else "#050505",
            fg_color=theme.WARN if busy else theme.ACCENT,
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
                    text="  Offline  ",
                    text_color="#050505",
                    fg_color=theme.OFFLINE,
                )
        elif not status["models"]:
            text = "Ollama: ONLINE\nNo models yet —\npull one below."
            if not self._busy:
                self.hud_chip.configure(
                    text="  No model  ",
                    text_color="#050505",
                    fg_color=theme.WARN,
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
                    text="  Ready  ",
                    text_color=theme.TEXT_ON_ACCENT,
                    fg_color=theme.ACCENT,
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
