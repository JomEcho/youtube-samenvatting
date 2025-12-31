"""
YouTube Samenvatting - GUI Applicatie
Een Mac desktop app voor het maken van samenvattingen van YouTube videos.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import os
from pathlib import Path

# Load .env file first
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from youtube_samenvatting import (
    process_video, load_config, save_config, OUTPUT_DIR, chat_with_transcript
)
from docx import Document


class YouTubeSamenvattingApp:
    # Licht beige/taupe kleuren
    BG_COLOR = "#E8E0D8"
    BG_LIGHT = "#F5F0EB"
    BG_DARK = "#D5CCC2"
    TEXT_COLOR = "#5C534A"
    TEXT_LIGHT = "#5C534A"

    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Samenvatting")
        self.root.geometry("700x700")
        self.root.configure(bg=self.BG_COLOR)

        # Load saved config
        self.config = load_config()

        # Chat state - bewaar provider/model/key van samenvatting voor chat
        self.current_transcript = None
        self.current_provider = None
        self.current_model = None
        self.current_api_key = None
        self.chat_history = []

        # Main container
        container = tk.Frame(root, bg=self.BG_COLOR, padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        # Title
        title = tk.Label(
            container,
            text="YouTube Samenvatting",
            font=("Helvetica", 28, "bold"),
            bg=self.BG_COLOR,
            fg=self.TEXT_LIGHT
        )
        title.pack(pady=(0, 10))

        # Custom tab buttons (gecentreerd)
        tab_btn_frame = tk.Frame(container, bg=self.BG_COLOR)
        tab_btn_frame.pack(pady=(0, 10))

        self.summary_btn = tk.Button(
            tab_btn_frame,
            text="Samenvatting",
            font=("Helvetica", 12, "bold"),
            bg=self.BG_LIGHT,
            fg=self.TEXT_COLOR,
            relief="flat",
            padx=20,
            pady=8,
            command=lambda: self.switch_tab(0)
        )
        self.summary_btn.pack(side=tk.LEFT, padx=2)

        self.chat_btn = tk.Button(
            tab_btn_frame,
            text="Chat",
            font=("Helvetica", 12),
            bg=self.BG_DARK,
            fg="#999999",
            relief="flat",
            padx=20,
            pady=8,
            state="disabled",
            command=lambda: self.switch_tab(1)
        )
        self.chat_btn.pack(side=tk.LEFT, padx=2)

        # Content frames (zonder notebook)
        self.content_frame = tk.Frame(container, bg=self.BG_COLOR)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Samenvatting
        self.summary_tab = tk.Frame(self.content_frame, bg=self.BG_COLOR)

        # Tab 2: Chat
        self.chat_tab = tk.Frame(self.content_frame, bg=self.BG_COLOR)

        # Chat disabled by default
        self.chat_enabled = False

        # Build both tabs
        self.build_summary_tab()
        self.build_chat_tab()

        # Show summary tab initially
        self.switch_tab(0)

    def switch_tab(self, tab_index):
        """Switch between tabs."""
        # Hide all tabs
        self.summary_tab.pack_forget()
        self.chat_tab.pack_forget()

        if tab_index == 0:
            self.summary_tab.pack(fill=tk.BOTH, expand=True)
            self.summary_btn.configure(bg=self.BG_LIGHT, font=("Helvetica", 12, "bold"))
            self.chat_btn.configure(bg=self.BG_DARK, font=("Helvetica", 12))
        elif tab_index == 1:
            if not self.chat_enabled:
                return  # Chat nog niet beschikbaar
            self.chat_tab.pack(fill=tk.BOTH, expand=True)
            self.summary_btn.configure(bg=self.BG_DARK, font=("Helvetica", 12))
            self.chat_btn.configure(bg=self.BG_LIGHT, font=("Helvetica", 12, "bold"))

    def build_summary_tab(self):
        """Build the summary tab content."""
        container = self.summary_tab

        # URL Section
        url_label = tk.Label(container, text="YouTube URL", font=("Helvetica", 12, "bold"),
                            bg=self.BG_COLOR, fg=self.TEXT_LIGHT, anchor="w")
        url_label.pack(fill=tk.X, pady=(5, 2))

        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(container, textvariable=self.url_var, font=("Helvetica", 14))
        self.url_entry.pack(fill=tk.X, pady=(0, 10))
        self.url_entry.bind('<Return>', lambda e: self.start_processing())

        # Provider Section
        provider_label = tk.Label(container, text="Taalmodel", font=("Helvetica", 12, "bold"),
                                 bg=self.BG_COLOR, fg=self.TEXT_LIGHT, anchor="w")
        provider_label.pack(fill=tk.X, pady=(5, 2))

        self.provider_var = tk.StringVar(value="ollama")  # Default: gpt-oss:20b

        providers = [
            ("Ollama - gpt-oss:20b (max ~3 uur video)", "ollama"),
            ("Ollama - gemma2:9b (max ~30 min video)", "ollama_gemma"),
            ("OpenAI (GPT-4o-mini)", "openai"),
            ("Anthropic (Claude Sonnet 4)", "anthropic"),
        ]

        for text, value in providers:
            rb = tk.Radiobutton(
                container,
                text=text,
                value=value,
                variable=self.provider_var,
                command=self.on_provider_change,
                bg=self.BG_COLOR,
                fg=self.TEXT_LIGHT,
                selectcolor=self.BG_DARK,
                activebackground=self.BG_COLOR,
                activeforeground=self.TEXT_LIGHT,
                highlightthickness=0,
                anchor="w"
            )
            rb.pack(fill=tk.X)

        # API Keys worden geladen uit .env bestand
        self.openai_key_var = tk.StringVar(value=os.environ.get("OPENAI_API_KEY", ""))
        self.anthropic_key_var = tk.StringVar(value=os.environ.get("ANTHROPIC_API_KEY", ""))

        # Status
        self.status_var = tk.StringVar(value="Klaar om te beginnen")
        status_label = tk.Label(container, textvariable=self.status_var, bg=self.BG_COLOR, fg=self.TEXT_LIGHT)
        status_label.pack(pady=(10, 5))

        # Buttons Frame
        btn_frame = tk.Frame(container, bg=self.BG_COLOR)
        btn_frame.pack(pady=(0, 10))

        self.process_btn = tk.Button(
            btn_frame,
            text="Samenvatting Maken",
            command=self.start_processing,
            font=("Helvetica", 12),
            fg=self.TEXT_COLOR,
            highlightbackground=self.BG_COLOR,
            padx=15,
            pady=8
        )
        self.process_btn.pack(side=tk.LEFT, padx=5)

        open_folder_btn = tk.Button(
            btn_frame,
            text="Open Map",
            command=self.open_output_folder,
            font=("Helvetica", 12),
            fg=self.TEXT_COLOR,
            highlightbackground=self.BG_COLOR,
            padx=15,
            pady=8
        )
        open_folder_btn.pack(side=tk.LEFT, padx=5)

        # Result Section
        result_label = tk.Label(container, text="Resultaat", font=("Helvetica", 12, "bold"),
                               bg=self.BG_COLOR, fg=self.TEXT_LIGHT, anchor="w")
        result_label.pack(fill=tk.X, pady=(5, 2))

        result_frame = tk.Frame(container, bg=self.BG_COLOR)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.result_text = tk.Text(result_frame, height=8, wrap=tk.WORD, font=("Helvetica", 11), bg="#faf8f5")
        self.result_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = tk.Scrollbar(result_frame, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.configure(yscrollcommand=scrollbar.set)

        # Output folder info
        folder_label = tk.Label(
            container,
            text=f"Bestanden: {OUTPUT_DIR}",
            bg=self.BG_COLOR,
            fg=self.TEXT_LIGHT,
            font=("Helvetica", 10)
        )
        folder_label.pack()

        self.on_provider_change()

    def build_chat_tab(self):
        """Build the chat tab content."""
        container = self.chat_tab

        # Info label
        info_label = tk.Label(
            container,
            text="Stel vragen over de video (antwoorden zijn gebaseerd op het transcript)",
            font=("Helvetica", 11),
            bg=self.BG_COLOR,
            fg=self.TEXT_LIGHT
        )
        info_label.pack(pady=(10, 5))

        # Chat section label
        chat_label = tk.Label(container, text="Gesprek", font=("Helvetica", 12, "bold"),
                             bg=self.BG_COLOR, fg=self.TEXT_LIGHT, anchor="w")
        chat_label.pack(fill=tk.X, pady=(5, 2))

        # Chat history display
        chat_frame = tk.Frame(container, bg=self.BG_COLOR)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.chat_display = tk.Text(
            chat_frame,
            height=15,
            wrap=tk.WORD,
            font=("Helvetica", 11),
            state="disabled",
            bg="#faf8f5"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        chat_scrollbar = tk.Scrollbar(chat_frame, command=self.chat_display.yview)
        chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.configure(yscrollcommand=chat_scrollbar.set)

        # Configure tags for styling
        self.chat_display.tag_configure("user", foreground="#6b5344", font=("Helvetica", 11, "bold"))
        self.chat_display.tag_configure("assistant", foreground="#3d3530")
        self.chat_display.tag_configure("label", foreground="#8a7a6a", font=("Helvetica", 10))

        # Input frame
        input_frame = tk.Frame(container, bg=self.BG_COLOR)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        self.chat_input = tk.Entry(input_frame, font=("Helvetica", 12))
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.chat_input.bind('<Return>', lambda e: self.send_chat_message())

        self.send_btn = tk.Button(
            input_frame,
            text="Verstuur",
            command=self.send_chat_message,
            font=("Helvetica", 12),
            fg=self.TEXT_COLOR,
            highlightbackground=self.BG_COLOR,
            padx=15,
            pady=5
        )
        self.send_btn.pack(side=tk.LEFT)

        # Clear button
        clear_btn = tk.Button(
            input_frame,
            text="Wis chat",
            command=self.clear_chat,
            font=("Helvetica", 12),
            fg=self.TEXT_COLOR,
            highlightbackground=self.BG_COLOR,
            padx=10,
            pady=5
        )
        clear_btn.pack(side=tk.LEFT, padx=(10, 0))

        # Chat status
        self.chat_status_var = tk.StringVar(value="")
        chat_status_label = tk.Label(
            container,
            textvariable=self.chat_status_var,
            bg=self.BG_COLOR,
            fg=self.TEXT_LIGHT
        )
        chat_status_label.pack()

    def on_provider_change(self):
        provider = self.provider_var.get()
        if provider == "ollama":
            self.status_var.set("Ollama gpt-oss:20b geselecteerd")
        elif provider == "ollama_gemma":
            self.status_var.set("Ollama gemma2:9b geselecteerd")
        elif provider == "openai":
            self.status_var.set("OpenAI geselecteerd")
        elif provider == "anthropic":
            self.status_var.set("Anthropic geselecteerd")

    def open_output_folder(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(['open', str(OUTPUT_DIR)])

    def update_status(self, message):
        self.root.after(0, lambda: self.status_var.set(message))

    def start_processing(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Geen URL", "Voer een YouTube URL in.")
            return

        provider = self.provider_var.get()

        # Handle ollama variants
        model = None
        if provider == "ollama_gemma":
            provider = "ollama"
            model = "gemma2:9b"
        elif provider == "ollama":
            model = "gpt-oss:20b"

        api_key = None
        if provider == "openai":
            api_key = self.openai_key_var.get()
            if not api_key:
                messagebox.showwarning("API Key", "OpenAI API key is vereist.")
                return
        elif provider == "anthropic":
            api_key = self.anthropic_key_var.get()
            if not api_key:
                messagebox.showwarning("API Key", "Anthropic API key is vereist.")
                return

        # Bewaar provider/model/key VOOR thread start (voor chat later)
        self.current_provider = provider
        self.current_model = model
        self.current_api_key = api_key

        self.process_btn.configure(state="disabled")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Bezig met verwerken...\n")

        thread = threading.Thread(
            target=self.process_video_thread,
            args=(url, provider, api_key, model)
        )
        thread.daemon = True
        thread.start()

    def process_video_thread(self, url, provider, api_key, model=None):
        try:
            transcript_path, summary_path = process_video(
                url, provider, api_key, model=model,
                progress_callback=self.update_status
            )

            # Read Word document content for display
            doc = Document(summary_path)
            summary_content = '\n'.join([para.text for para in doc.paragraphs])

            self.root.after(0, lambda: self.processing_complete(
                transcript_path, summary_path, summary_content
            ))

        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.processing_error(msg))

    def processing_complete(self, transcript_path, summary_path, summary_content):
        self.process_btn.configure(state="normal")
        self.status_var.set("Klaar!")

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"BESTANDEN OPGESLAGEN:\n\n")
        self.result_text.insert(tk.END, f"Transcriptie:\n{transcript_path}\n\n")
        self.result_text.insert(tk.END, f"Samenvatting:\n{summary_path}\n\n")
        self.result_text.insert(tk.END, "-" * 40 + "\n\n")
        self.result_text.insert(tk.END, summary_content)

        self.url_var.set("")

        # Load transcript for chat and enable chat tab
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Skip the header (first lines until the separator)
                if "=" * 50 in content:
                    self.current_transcript = content.split("=" * 50, 1)[1].strip()
                else:
                    self.current_transcript = content

            # Clear previous chat and enable chat tab
            self.chat_history = []
            self.clear_chat()
            self.chat_enabled = True
            self.chat_btn.configure(state="normal", fg=self.TEXT_COLOR)
            self.chat_status_var.set("Chat beschikbaar - stel je vragen!")
        except Exception as e:
            self.chat_status_var.set(f"Chat niet beschikbaar: {e}")

    def processing_error(self, error_message):
        self.process_btn.configure(state="normal")
        self.status_var.set("Fout opgetreden")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"FOUT: {error_message}")

    def send_chat_message(self):
        """Send a chat message and get response."""
        question = self.chat_input.get().strip()
        if not question:
            return

        if not self.current_transcript:
            messagebox.showwarning("Geen transcript", "Maak eerst een samenvatting van een video.")
            return

        # Gebruik opgeslagen provider/model/key van de samenvatting
        provider = self.current_provider
        model = self.current_model
        api_key = self.current_api_key

        # Add user message to display
        self.add_chat_message("user", question)
        self.chat_input.delete(0, tk.END)

        # Disable input while processing
        self.send_btn.configure(state="disabled")
        self.chat_input.configure(state="disabled")
        self.chat_status_var.set("Bezig met antwoorden...")

        # Process in background thread
        thread = threading.Thread(
            target=self.chat_thread,
            args=(question, provider, api_key, model)
        )
        thread.daemon = True
        thread.start()

    def chat_thread(self, question, provider, api_key, model=None):
        """Background thread for chat processing."""
        try:
            # Maak kopie van chat_history voor thread-safety
            history_copy = list(self.chat_history)

            response = chat_with_transcript(
                self.current_transcript,
                question,
                history_copy,
                provider,
                api_key,
                model=model
            )

            # Update history en UI op main thread (thread-safe)
            self.root.after(0, lambda q=question, r=response: self.chat_response_complete(q, r))

        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.chat_response_error(msg))

    def chat_response_complete(self, question, response):
        """Handle successful chat response (runs on main thread)."""
        # Update chat history thread-safe op main thread
        self.chat_history.append({"role": "user", "content": question})
        self.chat_history.append({"role": "assistant", "content": response})

        # Beperk chat history tot laatste 50 berichten
        if len(self.chat_history) > 50:
            self.chat_history = self.chat_history[-50:]

        self.add_chat_message("assistant", response)
        self.send_btn.configure(state="normal")
        self.chat_input.configure(state="normal")
        self.chat_input.focus()
        self.chat_status_var.set("")

    def chat_response_error(self, error_message):
        """Handle chat error."""
        self.add_chat_message("assistant", f"Fout: {error_message}")
        self.send_btn.configure(state="normal")
        self.chat_input.configure(state="normal")
        self.chat_status_var.set("Fout opgetreden")

    def add_chat_message(self, role, content):
        """Add a message to the chat display."""
        self.chat_display.configure(state="normal")

        if role == "user":
            self.chat_display.insert(tk.END, "Jij:\n", "label")
            self.chat_display.insert(tk.END, f"{content}\n\n", "user")
        else:
            self.chat_display.insert(tk.END, "Assistent:\n", "label")
            self.chat_display.insert(tk.END, f"{content}\n\n", "assistant")

        self.chat_display.configure(state="disabled")
        self.chat_display.see(tk.END)

    def clear_chat(self):
        """Clear chat history and display."""
        self.chat_history = []
        self.chat_display.configure(state="normal")
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.configure(state="disabled")
        if self.current_transcript:
            self.chat_status_var.set("Chat gewist - stel nieuwe vragen!")


def main():
    root = tk.Tk()
    app = YouTubeSamenvattingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
