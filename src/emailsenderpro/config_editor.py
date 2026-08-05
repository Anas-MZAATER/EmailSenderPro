"""In-app configuration editor for managing saved credentials."""
import logging
import tkinter as tk
from tkinter import messagebox
import webbrowser

from emailsenderpro.core.config_manager import ConfigManager
from emailsenderpro.core.credential_manager import CredentialManager
from emailsenderpro.core.smtp_validator import validate_smtp

logger = logging.getLogger(__name__)


class ConfigEditor(tk.Toplevel):
    """Window to view, edit, or delete saved SMTP configuration."""

    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.parent = parent
        self.on_save = on_save
        self.config_manager = ConfigManager()
        self.credential_manager = CredentialManager()

        self.title("Manage Configuration")
        self.geometry("450x380")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._load_config()
        self.center_window()

    def _build_ui(self):
        header = tk.Label(
            self, text="Manage Configuration", font=("Segoe UI", 14, "bold"), fg="#2c3e50"
        )
        header.pack(pady=(20, 10))

        self.status_label = tk.Label(self, text="", font=("Segoe UI", 9))
        self.status_label.pack(pady=(0, 10))

        form = tk.Frame(self)
        form.pack(padx=40, pady=5, fill=tk.X)

        # Email
        tk.Label(form, text="Gmail Address:", font=("Segoe UI", 10), anchor="w").pack(
            fill=tk.X, pady=(5, 2)
        )
        self.email_var = tk.StringVar()
        tk.Entry(form, textvariable=self.email_var, font=("Segoe UI", 10)).pack(
            fill=tk.X, ipady=3
        )

        # Password
        tk.Label(form, text="Gmail App Password:", font=("Segoe UI", 10), anchor="w").pack(
            fill=tk.X, pady=(15, 2)
        )
        self.password_var = tk.StringVar()
        tk.Entry(form, textvariable=self.password_var, show="*", font=("Segoe UI", 10)).pack(
            fill=tk.X, ipady=3
        )

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=25)

        tk.Button(
            btn_frame,
            text="Gmail Guide",
            command=lambda: webbrowser.open(
                "https://support.google.com/accounts/answer/185833"
            ),
            width=12,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame, text="Delete Config", command=self._on_delete, width=12, fg="#e74c3c"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Cancel", command=self.destroy, width=10).pack(
            side=tk.LEFT, padx=5
        )

        self.save_btn = tk.Button(
            btn_frame,
            text="Save Changes",
            command=self._on_save,
            width=12,
            bg="#27ae60",
            fg="white",
            activebackground="#219a52",
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _load_config(self):
        email = self.config_manager.get("email", "")
        if email:
            self.email_var.set(email)
            password = self.credential_manager.get_password(email) or ""
            self.password_var.set(password)
            self.status_label.config(
                text=f"Configuration found: {email}", fg="#27ae60"
            )
        else:
            self.status_label.config(text="No saved configuration found.", fg="#e74c3c")

    def _on_save(self):
        email = self.email_var.get().strip()
        password = self.password_var.get().strip()

        if not email or not password:
            messagebox.showwarning("Missing Fields", "Please fill in both fields.")
            return

        self.save_btn.config(state=tk.DISABLED, text="Validating...")
        self.update_idletasks()

        success, msg = validate_smtp(email, password)

        if success:
            self.config_manager.set("email", email)
            self.config_manager.set("server", "smtp.gmail.com")
            self.config_manager.set("port", 587)
            self.config_manager.save()
            self.credential_manager.save_password(email, password)

            self.status_label.config(text="Configuration updated!", fg="#27ae60")
            messagebox.showinfo("Success", "Configuration saved successfully!")

            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            self.status_label.config(text=msg, fg="#e74c3c")
            messagebox.showerror("SMTP Error", msg)
            self.save_btn.config(state=tk.NORMAL, text="Save Changes")

    def _on_delete(self):
        email = self.config_manager.get("email", "")
        if not email:
            messagebox.showinfo("No Config", "There is no configuration to delete.")
            return

        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the configuration for {email}?",
        ):
            self.credential_manager.delete_password(email)
            self.config_manager.clear()
            self.email_var.set("")
            self.password_var.set("")
            self.status_label.config(text="Configuration deleted.", fg="#e74c3c")
            messagebox.showinfo("Deleted", "Configuration has been removed.")
            if self.on_save:
                self.on_save()
