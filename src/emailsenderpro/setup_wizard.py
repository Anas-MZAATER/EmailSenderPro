#!/usr/bin/env python3
"""First-run configuration wizard."""
import logging
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

from emailsenderpro.core.config_manager import ConfigManager
from emailsenderpro.core.credential_manager import CredentialManager
from emailsenderpro.core.smtp_validator import validate_smtp, SMTPValidationError

logger = logging.getLogger(__name__)


class SetupWizard(tk.Tk):
    """Modern ttk setup window for Gmail credentials."""

    def __init__(self):
        super().__init__()
        self.title("First Time Configuration")
        self.geometry("520x420")
        self.resizable(False, False)

        self.email_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.show_pass = tk.BooleanVar(value=False)
        self.remember_var = tk.BooleanVar(value=True)

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        frame = ttk.Frame(self, padding="25")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Email Sender Pro", font=("Segoe UI", 18, "bold")).pack(pady=(0, 5))
        ttk.Label(frame, text="Enter your Gmail credentials to get started.").pack(pady=(0, 20))

        ttk.Label(frame, text="Gmail Address:").pack(anchor=tk.W)
        ttk.Entry(frame, textvariable=self.email_var, width=45).pack(fill=tk.X, pady=(0, 12))

        ttk.Label(frame, text="Gmail App Password:").pack(anchor=tk.W)
        pass_frame = ttk.Frame(frame)
        pass_frame.pack(fill=tk.X, pady=(0, 5))
        self.pass_entry = ttk.Entry(pass_frame, textvariable=self.pass_var, show="*", width=38)
        self.pass_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(pass_frame, text="Show", width=6, command=self._toggle_pass).pack(side=tk.LEFT, padx=(5, 0))

        ttk.Checkbutton(frame, text="Remember this account", variable=self.remember_var).pack(anchor=tk.W, pady=8)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(25, 0))
        ttk.Button(btn_frame, text="Gmail Guide", command=self._open_guide).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Cancel", command=self._on_close).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.RIGHT)

        self.bind("<Return>", lambda _e: self._save())

    def _toggle_pass(self):
        self.show_pass.set(not self.show_pass.get())
        self.pass_entry.config(show="" if self.show_pass.get() else "*")

    def _open_guide(self):
        webbrowser.open("https://support.google.com/accounts/answer/185833")

    def _save(self):
        email = self.email_var.get().strip()
        password = self.pass_var.get().strip()

        if not email or "@" not in email or "." not in email:
            messagebox.showerror("Invalid Input", "Please enter a valid Gmail address.")
            return
        if not password:
            messagebox.showerror("Invalid Input", "App password is required.")
            return

        try:
            validate_smtp(email, password)
        except SMTPValidationError as exc:
            messagebox.showerror("SMTP Authentication Failed", str(exc))
            return

        try:
            ConfigManager.set_email(email)
            if self.remember_var.get():
                CredentialManager.save_password(password)
            messagebox.showinfo("Success", "Configuration saved successfully!")
            logger.info("Setup wizard completed for %s", email)
            self.destroy()
        except Exception as exc:
            logger.exception("Failed to save configuration")
            messagebox.showerror("Error", f"Could not save configuration:\n{exc}")

    def _on_close(self):
        self.destroy()
