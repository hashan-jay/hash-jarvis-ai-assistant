"""CustomTkinter chat UI for HASH-JARVIS."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

import config
from backend.chat_service import ChatService


class HashJarvisApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode(config.APPEARANCE_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)

        self.title(config.APP_TITLE)
        self.geometry(config.APP_GEOMETRY)
        self.minsize(900, 600)

        self.service = ChatService()
        self._busy = False
        self._assistant_bubble: Optional[ctk.CTkTextbox] = None

        self._build_layout()
        self.refresh_status()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text=config.ASSISTANT_NAME,
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(padx=16, pady=(20, 4), anchor="w")

        ctk.CTkLabel(
            self.sidebar,
            text="At your service · Local · Private",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65"),
        ).pack(padx=16, pady=(0, 16), anchor="w")

        self.new_chat_btn = ctk.CTkButton(
            self.sidebar, text="New Chat", command=self.on_new_chat
        )
        self.new_chat_btn.pack(padx=16, pady=6, fill="x")

        self.refresh_btn = ctk.CTkButton(
            self.sidebar,
            text="Refresh Models",
            fg_color="transparent",
            border_width=1,
            command=self.refresh_status,
        )
        self.refresh_btn.pack(padx=16, pady=6, fill="x")

        ctk.CTkLabel(self.sidebar, text="Model", anchor="w").pack(
            padx=16, pady=(18, 4), fill="x"
        )
        self.model_menu = ctk.CTkOptionMenu(
            self.sidebar, values=["No models found"], command=self.on_model_change
        )
        self.model_menu.pack(padx=16, pady=4, fill="x")

        ctk.CTkLabel(self.sidebar, text="Pull model", anchor="w").pack(
            padx=16, pady=(16, 4), fill="x"
        )
        self.pull_entry = ctk.CTkEntry(
            self.sidebar, placeholder_text="e.g. llama3.2:3b"
        )
        self.pull_entry.pack(padx=16, pady=4, fill="x")
        self.pull_entry.insert(0, config.DEFAULT_MODEL)

        self.pull_btn = ctk.CTkButton(
            self.sidebar, text="Download Model", command=self.on_pull_model
        )
        self.pull_btn.pack(padx=16, pady=6, fill="x")

        self.memory_switch = ctk.CTkSwitch(
            self.sidebar,
            text="ChromaDB Memory",
            command=self.on_toggle_memory,
        )
        self.memory_switch.pack(padx=16, pady=(20, 6), anchor="w")
        if config.ENABLE_MEMORY_BY_DEFAULT:
            self.memory_switch.select()

        self.clear_memory_btn = ctk.CTkButton(
            self.sidebar,
            text="Clear Memory",
            fg_color="transparent",
            border_width=1,
            command=self.on_clear_memory,
        )
        self.clear_memory_btn.pack(padx=16, pady=6, fill="x")

        self.status_label = ctk.CTkLabel(
            self.sidebar,
            text="Checking Ollama...",
            wraplength=210,
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(padx=16, pady=(24, 16), fill="x", side="bottom")

        # Main chat area
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_rowconfigure(0, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        self.chat_frame = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        self.chat_frame.grid(row=0, column=0, sticky="nsew", padx=18, pady=(18, 8))
        self.chat_frame.grid_columnconfigure(0, weight=1)

        self.composer = ctk.CTkFrame(self.main)
        self.composer.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 18))
        self.composer.grid_columnconfigure(0, weight=1)

        self.input_box = ctk.CTkTextbox(self.composer, height=90)
        self.input_box.grid(row=0, column=0, sticky="ew", padx=(12, 8), pady=12)
        self.input_box.bind("<Control-Return>", self._on_ctrl_enter)

        self.send_btn = ctk.CTkButton(
            self.composer, text="Send", width=100, command=self.on_send
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
        note = ctk.CTkLabel(
            self.chat_frame,
            text=text,
            justify="left",
            anchor="w",
            wraplength=720,
            text_color=("gray30", "gray70"),
        )
        note.grid(sticky="ew", pady=(0, 12))

    def _add_bubble(self, role: str, text: str = "") -> ctk.CTkTextbox:
        is_user = role == "user"
        outer = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        outer.grid(sticky="ew", pady=6)
        outer.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            outer,
            text="You" if is_user else config.ASSISTANT_NAME,
            anchor="e" if is_user else "w",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        label.grid(row=0, column=0, sticky="e" if is_user else "w", padx=4)

        bubble = ctk.CTkTextbox(
            outer,
            height=40,
            wrap="word",
            activate_scrollbars=False,
            fg_color=("#dbeafe", "#1f2937") if is_user else ("#f3f4f6", "#111827"),
        )
        bubble.grid(row=1, column=0, sticky="ew", padx=(80, 0) if is_user else (0, 80))
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
            text = "Ollama: offline\nStart the Ollama app or run `ollama serve`."
        elif not status["models"]:
            text = "Ollama: online\nNo models yet — pull one below."
        else:
            memory = "on" if status["memory_enabled"] else "off"
            text = (
                f"Ollama: online\n"
                f"Model: {self.service.model}\n"
                f"Memory: {memory}"
            )
            if status["memory_error"]:
                text += f"\nMemory note: {status['memory_error'][:80]}"

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
