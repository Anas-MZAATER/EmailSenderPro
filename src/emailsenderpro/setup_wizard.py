"""First-run configuration wizard with SMTP validation."""
import logging
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

from emailsenderpro.core.config_manager import ConfigManager
from emailsenderpro.core.credential_manager import CredentialManager
from emailsenderpro.core.smtp_validator import validate_smtp

logger = logging.getLogger(__name__)


class SetupWizard(tk.Toplevel):
    """Setup wizard for first-time configuration."""

    def __init__(self, parent, on_complete=None):
        super().__init__(parent)
        self.parent = parent
        self.on_complete = on_complete
        self.config_manager = ConfigManager()
        self.credential_manager = CredentialManager()

        self.title("EmailSenderPro - First Time Configuration")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self.center_window()

    def _build_ui(self):
        # Header
        header = tk.Label(
            self,
            text="Welcome to EmailSenderPro",
            font=("Segoe UI", 16, "bold"),
            fg="#2c3e50",
        )
        header.pack(pady=(20, 10))

        sub = tk.Label(
            self,
            text="Configure your Gmail account to get started.",
            font=("Segoe UI", 10),
            fg="#7f8c8d",
        )
        sub.pack(pady=(0, 20))

        # Form frame
        form = tk.Frame(self)
        form.pack(padx=40, pady=10, fill=tk.X)

        # Email
        tk.Label(form, text="Gmail Address:", font=("Segoe UI", 10), anchor="w").pack(
            fill=tk.X, pady=(10, 2)
        )
        self.email_var = tk.StringVar()
        self.email_entry = tk.Entry(form, textvariable=self.email_var, font=("Segoe UI", 10))
        self.email_entry.pack(fill=tk.X, ipady=4)

        # Password
        tk.Label(form, text="Gmail App Password:", font=("Segoe UI", 10), anchor="w").pack(
            fill=tk.X, pady=(15, 2)
        )
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(
            form, textvariable=self.password_var, show="*", font=("Segoe UI", 10)
        )
        self.password_entry.pack(fill=tk.X, ipady=4)

        hint = tk.Label(
            form,
            text="Not your regular password. Generate an App Password in Google Account settings.",
            font=("Segoe UI", 8),
            fg="#95a5a6",
            wraplength=420,
            justify=tk.LEFT,
        )
        hint.pack(fill=tk.X, pady=(2, 0))

        # Remember checkbox
        self.remember_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            form, text="Remember this account", variable=self.remember_var, font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(15, 0))

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=30)

        tk.Button(
            btn_frame,
            text="Gmail Guide",
            command=lambda: webbrowser.open(
                "https://support.google.com/accounts/answer/185833"
            ),
            width=12,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            width=10,
        ).pack(side=tk.LEFT, padx=5)

        self.save_btn = tk.Button(
            btn_frame,
            text="Save",
            command=self._on_save,
            width=10,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_label = tk.Label(self, text="", font=("Segoe UI", 9))
        self.status_label.pack(pady=(5, 0))

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _on_save(self):
        email = self.email_var.get().strip()
        password = self.password_var.get().strip()

        if not email or not password:
            messagebox.showwarning("Missing Fields", "Please enter both email and password.")
            return

        if "@" not in email:
            messagebox.showwarning("Invalid Email", "Please enter a valid email address.")
            return

        self.save_btn.config(state=tk.DISABLED, text="Validating...")
        self.status_label.config(text="Testing SMTP connection...", fg="#3498db")
        self.update_idletasks()

        success, msg = validate_smtp(email, password)

        if success:
            self.config_manager.set("email", email)
            self.config_manager.set("server", "smtp.gmail.com")
            self.config_manager.set("port", 587)
            self.config_manager.save()

            if self.remember_var.get():
                self.credential_manager.save_password(email, password)

            self.status_label.config(text="Configuration saved successfully!", fg="#27ae60")
            messagebox.showinfo("Success", "Your account has been configured successfully!")

            if self.on_complete:
                self.on_complete()
            self.destroy()
        else:
            self.status_label.config(text=msg, fg="#e74c3c")
            messagebox.showerror("SMTP Error", msg)
            self.save_btn.config(state=tk.NORMAL, text="Save")
