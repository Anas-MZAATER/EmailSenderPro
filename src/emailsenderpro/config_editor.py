"""In-app configuration editor for managing multiple saved credentials."""
import logging
import tkinter as tk
from tkinter import messagebox
import webbrowser

from emailsenderpro.core.config_manager import ConfigManager
from emailsenderpro.core.credential_manager import CredentialManager
from emailsenderpro.core.smtp_validator import validate_smtp

logger = logging.getLogger(__name__)


class ConfigEditor(tk.Toplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.parent = parent
        self.on_save = on_save
        self.config_manager = ConfigManager()
        self.credential_manager = CredentialManager()

        self.title("Manage Configuration")
        self.geometry("550x440")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._load_accounts()
        self.center_window()
        self.focus_force()

    def _build_ui(self):
        tk.Label(self, text="Manage Configuration", font=("Segoe UI", 14, "bold"), fg="#2c3e50").pack(pady=(12, 5))
        self.status_label = tk.Label(self, text="", font=("Segoe UI", 9))
        self.status_label.pack(pady=(0, 6))

        main = tk.Frame(self)
        main.pack(padx=15, pady=5, fill=tk.BOTH, expand=True)
        main.columnconfigure(1, weight=1)

        # Left: account list
        list_frame = tk.LabelFrame(main, text="Saved Accounts", font=("Segoe UI", 9, "bold"), padx=5, pady=5)
        list_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        self.accounts_list = tk.Listbox(list_frame, width=24, height=10, font=("Segoe UI", 9))
        self.accounts_list.pack(fill=tk.BOTH, expand=True)
        self.accounts_list.bind("<<ListboxSelect>>", self._on_select_account)

        lb = tk.Frame(list_frame)
        lb.pack(fill=tk.X, pady=(5, 0))
        tk.Button(lb, text="Add New", command=self._add_new_account, width=10).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(lb, text="Delete", command=self._delete_account, width=10, fg="#e74c3c").pack(side=tk.LEFT)

        # Right: edit form
        form_frame = tk.LabelFrame(main, text="Account Details", font=("Segoe UI", 9, "bold"), padx=10, pady=8)
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.columnconfigure(1, weight=1)

        tk.Label(form_frame, text="Gmail Address:", font=("Segoe UI", 9), anchor="w").grid(row=0, column=0, sticky="w", pady=(5, 2))
        self.email_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.email_var, font=("Segoe UI", 9)).grid(row=0, column=1, sticky="ew", ipady=2, pady=(5, 2))

        tk.Label(form_frame, text="App Password:", font=("Segoe UI", 9), anchor="w").grid(row=1, column=0, sticky="w", pady=(10, 2))
        pw_frame = tk.Frame(form_frame)
        pw_frame.grid(row=1, column=1, sticky="ew", pady=(10, 2))
        pw_frame.columnconfigure(0, weight=1)

        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(pw_frame, textvariable=self.password_var, show="*", font=("Segoe UI", 9))
        self.password_entry.grid(row=0, column=0, sticky="ew", ipady=2)
        self.show_pw_btn = tk.Button(pw_frame, text="👁 Show", command=self._toggle_password, width=8, font=("Segoe UI", 8))
        self.show_pw_btn.grid(row=0, column=1, padx=(4, 0))

        tk.Label(form_frame, text="Server:", font=("Segoe UI", 9), anchor="w").grid(row=2, column=0, sticky="w", pady=(10, 2))
        self.server_var = tk.StringVar(value="smtp.gmail.com")
        tk.Entry(form_frame, textvariable=self.server_var, font=("Segoe UI", 9)).grid(row=2, column=1, sticky="ew", ipady=2, pady=(10, 2))

        tk.Label(form_frame, text="Port:", font=("Segoe UI", 9), anchor="w").grid(row=3, column=0, sticky="w", pady=(10, 2))
        self.port_var = tk.StringVar(value="587")
        tk.Entry(form_frame, textvariable=self.port_var, font=("Segoe UI", 9), width=8).grid(row=3, column=1, sticky="w", ipady=2, pady=(10, 2))

        tk.Label(form_frame, text="Use an App Password, not your regular Gmail password.",
                 font=("Segoe UI", 8), fg="#95a5a6", wraplength=280, justify=tk.LEFT).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))

        btn_frame = tk.Frame(form_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(15, 0), sticky="w")
        tk.Button(btn_frame, text="Gmail Guide", command=lambda: webbrowser.open("https://support.google.com/accounts/answer/185833"), width=11).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(btn_frame, text="Cancel", command=self.destroy, width=10).pack(side=tk.LEFT, padx=(0, 6))
        self.save_btn = tk.Button(btn_frame, text="Save Account", command=self._on_save, width=12, bg="#27ae60", fg="white", activebackground="#219a52")
        self.save_btn.pack(side=tk.LEFT)

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _toggle_password(self):
        if self.password_entry.cget("show") == "*":
            self.password_entry.config(show="")
            self.show_pw_btn.config(text="🙈 Hide")
        else:
            self.password_entry.config(show="*")
            self.show_pw_btn.config(text="👁 Show")

    def _load_accounts(self):
        self.accounts_list.delete(0, tk.END)
        accounts = self.config_manager.get_accounts()
        if not accounts:
            self.status_label.config(text="No saved accounts.", fg="#e74c3c")
            return
        for acc in accounts:
            self.accounts_list.insert(tk.END, acc.get("email", "unknown"))
        self.status_label.config(text=f"{len(accounts)} account(s) saved.", fg="#27ae60")

    def _on_select_account(self, event=None):
        sel = self.accounts_list.curselection()
        if not sel:
            return
        email = self.accounts_list.get(sel[0])
        acc = self.config_manager.get_account(email)
        if acc:
            self.email_var.set(acc.get("email", ""))
            self.server_var.set(acc.get("server", "smtp.gmail.com"))
            self.port_var.set(str(acc.get("port", 587)))
            password = self.credential_manager.get_password(email) or ""
            self.password_var.set(password)

    def _add_new_account(self):
        self.accounts_list.selection_clear(0, tk.END)
        self.email_var.set("")
        self.password_var.set("")
        self.server_var.set("smtp.gmail.com")
        self.port_var.set("587")
        self.status_label.config(text="Fill in the form and click Save Account.", fg="#3498db")

    def _delete_account(self):
        sel = self.accounts_list.curselection()
        if not sel:
            messagebox.showinfo("Select First", "Click on an account in the list to select it, then click Delete.")
            return
        email = self.accounts_list.get(sel[0])
        if messagebox.askyesno("Confirm Delete", f"Delete account {email}?"):
            self.credential_manager.delete_password(email)
            self.config_manager.remove_account(email)
            self.config_manager.save()
            self._load_accounts()
            self.email_var.set("")
            self.password_var.set("")
            self.status_label.config(text=f"Deleted {email}.", fg="#e74c3c")
            if self.on_save:
                self.on_save()

    def _on_save(self):
        email = self.email_var.get().strip()
        password = self.password_var.get().strip()
        server = self.server_var.get().strip()
        try:
            port = int(self.port_var.get().strip())
        except ValueError:
            messagebox.showwarning("Invalid Port", "Port must be a number.")
            return

        if not email or not password:
            messagebox.showwarning("Missing Fields", "Please enter both email and password.")
            return
        if "@" not in email:
            messagebox.showwarning("Invalid Email", "Please enter a valid email address.")
            return

        self.save_btn.config(state=tk.DISABLED, text="Validating...")
        self.status_label.config(text="Testing SMTP connection...", fg="#3498db")
        self.update_idletasks()

        success, msg = validate_smtp(email, password, server, port)

        if success:
            account = {"email": email, "server": server, "port": port}
            self.config_manager.add_account(account)
            self.config_manager.save()
            self.credential_manager.save_password(email, password)
            self.save_btn.config(state=tk.NORMAL, text="Save Account")
            self.status_label.config(text=f"Saved: {email}", fg="#27ae60")
            self._load_accounts()
            for i in range(self.accounts_list.size()):
                if self.accounts_list.get(i) == email:
                    self.accounts_list.selection_set(i)
                    break
            if self.on_save:
                self.on_save()
        else:
            self.save_btn.config(state=tk.NORMAL, text="Save Account")
            self.status_label.config(text=msg, fg="#e74c3c")
            messagebox.showerror("SMTP Error", msg)
