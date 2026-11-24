"""Tkinter GUI for the personal voice assistant."""

from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog

# Load environment variables for LLM API keys
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from assistant_core import VoiceAssistant

# Color Scheme - Professional Dark Theme
BG_PRIMARY = "#1e1e1e"      # Dark background
BG_SECONDARY = "#2d2d2d"    # Slightly lighter
TEXT_PRIMARY = "#e0e0e0"    # Light gray text
TEXT_SECONDARY = "#b0b0b0"  # Dimmed text
ACCENT_BLUE = "#0084d4"     # Primary action
ACCENT_GREEN = "#10b981"    # Success/Listening
ACCENT_RED = "#ef4444"      # Stop/Alert
ACCENT_ORANGE = "#f59e0b"   # Warning
BORDER_COLOR = "#3d3d3d"    # Borders


class StyledButton(tk.Button):
    """Custom button with professional styling."""

    def __init__(self, parent, text, command=None, style="primary", **kwargs):
        colors = {
            "primary": (ACCENT_BLUE, "white"),
            "success": (ACCENT_GREEN, "white"),
            "danger": (ACCENT_RED, "white"),
            "secondary": (BG_SECONDARY, TEXT_PRIMARY),
        }
        fg_color, text_color = colors.get(style, colors["primary"])

        super().__init__(
            parent,
            text=text,
            command=command,
            bg=fg_color,
            fg=text_color,
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=8,
            cursor="hand2",
            activebackground=self._darken(fg_color),
            activeforeground=text_color,
            **kwargs,
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.base_bg = fg_color
        self.base_fg = text_color

    def _darken(self, color):
        # Simple darkening effect
        return color

    def _on_enter(self, event):
        self.config(relief=tk.RAISED)

    def _on_leave(self, event):
        self.config(relief=tk.FLAT)


class AssistantGUI:
    """Professional desktop interface for the voice assistant."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Voice Assistant")
        self.root.geometry("900x680")
        self.root.minsize(800, 600)
        self.root.configure(bg=BG_PRIMARY)

        # Apply custom styles
        self._configure_styles()

        self.assistant = VoiceAssistant()
        self.listening = False
        self.listen_thread: threading.Thread | None = None

        self._build_interface()
        self._log("🤖 Assistant ready. Use the text box or click Start Listening.")

    def _configure_styles(self) -> None:
        """Configure global style settings."""
        self.root.option_add("*Background", BG_PRIMARY)
        self.root.option_add("*Foreground", TEXT_PRIMARY)
        self.root.option_add("*Font", ("Segoe UI", 9))

    def _build_interface(self) -> None:
        """Build the professional UI layout."""
        # Header Section
        self._build_header()

        # Main content area
        content_frame = tk.Frame(self.root, bg=BG_PRIMARY)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Chat display area
        self._build_chat_area(content_frame)

        # Input section
        self._build_input_section(content_frame)

        # Controls section
        self._build_controls_section(content_frame)

        # Status bar
        self._build_status_bar()

    def _build_header(self) -> None:
        """Build the header section with title and status."""
        header_frame = tk.Frame(self.root, bg=BG_SECONDARY, height=70)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)

        # Title and status container
        title_container = tk.Frame(header_frame, bg=BG_SECONDARY)
        title_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        title = tk.Label(
            title_container,
            text="🎙️ Personal Voice Assistant",
            font=("Segoe UI", 22, "bold"),
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
        )
        title.pack(side=tk.LEFT, anchor=tk.W)

        # Status indicator
        self.status_indicator = tk.Label(
            title_container,
            text="● Ready",
            font=("Segoe UI", 10),
            bg=BG_SECONDARY,
            fg=ACCENT_GREEN,
        )
        self.status_indicator.pack(side=tk.RIGHT, anchor=tk.E)

        # Divider
        divider = tk.Frame(self.root, bg=BORDER_COLOR, height=2)
        divider.pack(fill=tk.X)

    def _build_chat_area(self, parent) -> None:
        """Build the chat display area."""
        chat_container = tk.Frame(parent, bg=BG_PRIMARY)
        chat_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Chat label
        chat_label = tk.Label(
            chat_container,
            text="Conversation",
            font=("Segoe UI", 11, "bold"),
            bg=BG_PRIMARY,
            fg=TEXT_PRIMARY,
        )
        chat_label.pack(anchor=tk.W, pady=(0, 8))

        # Chat area with custom styling
        self.log_area = scrolledtext.ScrolledText(
            chat_container,
            wrap=tk.WORD,
            height=20,
            font=("Segoe UI", 10),
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
            insertbackground=ACCENT_BLUE,
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.configure(state=tk.DISABLED)

        # Configure tags for styling
        self.log_area.tag_config("user", foreground=ACCENT_BLUE, font=("Segoe UI", 10, "bold"))
        self.log_area.tag_config("assistant", foreground=ACCENT_GREEN, font=("Segoe UI", 10, "bold"))
        self.log_area.tag_config("security", foreground=ACCENT_ORANGE)
        self.log_area.tag_config("error", foreground=ACCENT_RED)

    def _build_input_section(self, parent) -> None:
        """Build the input section."""
        input_container = tk.Frame(parent, bg=BG_PRIMARY)
        input_container.pack(fill=tk.X, padx=15, pady=(0, 10))

        input_label = tk.Label(
            input_container,
            text="Type a command",
            font=("Segoe UI", 11, "bold"),
            bg=BG_PRIMARY,
            fg=TEXT_PRIMARY,
        )
        input_label.pack(anchor=tk.W, pady=(0, 8))

        input_frame = tk.Frame(input_container, bg=BG_PRIMARY)
        input_frame.pack(fill=tk.X)

        self.command_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 11),
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
            insertbackground=ACCENT_BLUE,
            relief=tk.FLAT,
            border=0,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_BLUE,
        )
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, ipadx=10)
        self.command_entry.bind("<Return>", lambda _event: self.handle_text_command())

        send_button = StyledButton(
            input_frame,
            "Send",
            command=self.handle_text_command,
            style="primary",
            width=8,
        )
        send_button.pack(side=tk.LEFT, padx=(10, 0))

    def _build_controls_section(self, parent) -> None:
        """Build the control buttons section."""
        controls_container = tk.Frame(parent, bg=BG_PRIMARY)
        controls_container.pack(fill=tk.X, padx=15, pady=(0, 15))

        controls_label = tk.Label(
            controls_container,
            text="Controls",
            font=("Segoe UI", 11, "bold"),
            bg=BG_PRIMARY,
            fg=TEXT_PRIMARY,
        )
        controls_label.pack(anchor=tk.W, pady=(0, 8))

        button_frame = tk.Frame(controls_container, bg=BG_PRIMARY)
        button_frame.pack(fill=tk.X)

        self.listen_button = StyledButton(
            button_frame,
            "🎤 Start Listening",
            command=self.toggle_listening,
            style="success",
        )
        self.listen_button.pack(side=tk.LEFT, padx=(0, 8))

        clear_button = StyledButton(
            button_frame,
            "🗑️  Clear Chat",
            command=self.clear_chat,
            style="secondary",
        )
        clear_button.pack(side=tk.LEFT, padx=(0, 8))

        threshold_button = StyledButton(
            button_frame,
            "🔊 Mic Sensitivity",
            command=self.set_threshold,
            style="secondary",
        )
        threshold_button.pack(side=tk.LEFT)

    def _build_status_bar(self) -> None:
        """Build the status bar at the bottom."""
        status_frame = tk.Frame(self.root, bg=BG_SECONDARY, height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(
            status_frame,
            text="Ready to assist",
            font=("Segoe UI", 9),
            bg=BG_SECONDARY,
            fg=TEXT_SECONDARY,
            padx=15,
        )
        self.status_label.pack(side=tk.LEFT, anchor=tk.W, fill=tk.BOTH, expand=True)

    def _log(self, message: str, tag: str = "normal") -> None:
        """Add message to chat area with optional tag styling."""
        self.log_area.configure(state=tk.NORMAL)
        if tag != "normal":
            self.log_area.insert(tk.END, f"{message}\n", tag)
        else:
            self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state=tk.DISABLED)

    def _update_status(self, message: str, indicator_color: str = TEXT_SECONDARY) -> None:
        """Update status bar and indicator."""
        self.status_label.configure(text=message)
        self.status_indicator.configure(fg=indicator_color)

    def clear_chat(self) -> None:
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.delete("1.0", tk.END)
        self.log_area.configure(state=tk.DISABLED)
        self._update_status("Chat cleared")

    def handle_text_command(self) -> None:
        command = self.command_entry.get().strip()
        if not command:
            return

        self.command_entry.delete(0, tk.END)
        self._process_command(command)

    def toggle_listening(self) -> None:
        if self.listening:
            self.listening = False
            self.listen_button.configure(text="🎤 Start Listening")
            self._update_status("Listening stopped", ACCENT_GREEN)
            self._log("🛑 Assistant stopped listening.")
            return

        if self.assistant.recognizer is None:
            messagebox.showwarning(
                "Voice Input Unavailable",
                "SpeechRecognition is not installed.",
            )
            return

        try:
            self._update_status("Calibrating microphone...", ACCENT_ORANGE)
            self.assistant.calibrate_microphone()
        except RuntimeError as exc:
            messagebox.showerror("Microphone Error", str(exc))
            self._update_status("Microphone error", ACCENT_RED)
            return

        self.listening = True
        self.listen_button.configure(text="⏹️  Stop Listening")
        self._update_status("Listening...", ACCENT_GREEN)
        self._log("🎤 Assistant is now listening.")

        if self.listen_thread is None or not self.listen_thread.is_alive():
            self.listen_thread = threading.Thread(target=self._listen_in_background, daemon=True)
            self.listen_thread.start()

    def set_threshold(self) -> None:
        value = simpledialog.askinteger(
            "Mic Sensitivity",
            "Enter a sensitivity value (lower = more sensitive, example: 300):",
            initialvalue=self.assistant.threshold,
            minvalue=50,
            maxvalue=5000,
        )
        if value is None:
            return

        self.assistant.threshold = value
        if self.assistant.recognizer is not None:
            self.assistant.recognizer.energy_threshold = value
        self._log(f"🔊 Microphone sensitivity set to {value}.")
        self._update_status(f"Sensitivity: {value}")

    def _listen_in_background(self) -> None:
        while self.listening:
            try:
                self._update_status("🎤 Listening... Speak now!", ACCENT_GREEN)
                command = self.assistant.listen()
            except RuntimeError as exc:
                self.root.after(0, lambda error=str(exc): self._handle_listen_error(error))
                break

            if not self.listening:
                break

            if not command:
                self._update_status("❓ Could not hear you. Retry...", ACCENT_ORANGE)
                self.root.after(0, lambda: self._log("⚠️  Could not recognize speech. Please speak clearly and try again."))
                self.root.after(2000, lambda: self._update_status("🎤 Listening... Speak now!", ACCENT_GREEN))
                continue

            self._update_status("⚙️ Processing...", ACCENT_BLUE)
            response = self.assistant.process_command(command)

            self.root.after(0, self._deliver_turn, command, response)

    def _process_command(self, command: str) -> None:
        self._update_status("Processing...", ACCENT_BLUE)
        response = self.assistant.process_command(command)
        self._deliver_turn(command, response)

        if response.should_exit:
            self.listening = False
            self.root.after(0, self.root.destroy)

    def _deliver_turn(self, command: str, response) -> None:
        self._log_turn(command, response.text)
        self._speak_message(response.text)
        self._update_status("Ready to assist", ACCENT_GREEN)

        if response.should_exit:
            self.listening = False
            self._reset_listening_state()
            self.root.after(0, self.root.destroy)

    def _speak_message(self, message: str) -> None:
        self.assistant.speak(message)

    def _log_turn(self, command: str, response_text: str) -> None:
        self._log(f"You: {command}", "user")
        decision = self.assistant.last_security_decision
        if decision is not None:
            status = "✅ ALLOWED" if decision.allowed else "🛡️  BLOCKED"
            security_msg = (
                f"Security: {status} | Threat: {decision.threat_probability * 100:.1f}% | "
                f"Time: {decision.latency_ms:.2f}ms | Source: {decision.source}"
            )
            self._log(security_msg, "security")
            if not decision.allowed:
                self._log(f"⚠️  Alert: {decision.reason}", "error")
            if decision.evidence:
                self._log(f"Evidence: {', '.join(decision.evidence)}", "security")
        self._log(f"Assistant: {response_text}", "assistant")

    def _reset_listening_state(self) -> None:
        self.listen_button.configure(text="🎤 Start Listening")

    def _handle_listen_error(self, error: str) -> None:
        self.listening = False
        self._reset_listening_state()
        self._update_status("Microphone error", ACCENT_RED)
        messagebox.showerror("Microphone Error", error)


def main() -> None:
    root = tk.Tk()
    AssistantGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
