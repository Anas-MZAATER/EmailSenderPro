#!/usr/bin/env python3
"""Main application dashboard (email sender GUI)."""
import json
import random
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path

from emailsenderpro.core.config_manager import ConfigManager
from emailsenderpro.core.credential_manager import CredentialManager
from emailsenderpro.services.excel_service import load_emails
from emailsenderpro.core.email_service import EmailService


class Dashboard(tk.Tk):
    """Primary application window for sending emails."""

    def __init__(self):
        super().__init__()
        self.title("Email Sender Pro")
        self.geometry("950x850")
        self.minsize(800, 700)

        root_dir = Path(__file__).resolve().parent.parent.parent
        default_csv = root_dir / "examples" / "emails.example.csv"
        default_body = root_dir / "examples" / "body.txt"

        self.file_path = tk.StringVar(value=str(default_csv) if default_csv.exists() else "")
        self.column_name = tk.StringVar(value="email")
        self.subject = tk.StringVar()
        self.body_text = tk.StringVar()
        self.body_file_path = tk.StringVar(value=str(default_body) if default_body.exists() else "")
        self.delay_min = tk.IntVar(value=300)
        self.delay_max = tk.IntVar(value=600)
        self.shuffle_var = tk.BooleanVar(value=True)
        self.html_var = tk.BooleanVar(value=False)
        self.dry_run_var = tk.BooleanVar(value=False)
        self.resume_var = tk.BooleanVar(value=True)
        self.rotation_mode = tk.StringVar(value="round_robin")

        self.attachments: list[str] = []
        self.sent_file = "sent.json"
        self.is_running = False
        self.stop_requested = False

        self.body_file_path.trace_add("write", self._auto_detect_html)

        self._build_ui()
        self._load_account_from_config()

    # --- Le reste de la classe reste inchangé ---
    def _build_ui(self):
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        f = scrollable
        r = 0

        ttk.Label(f, text="Email file (CSV / Excel):", font=("Segoe UI", 10, "bold")).grid(
            row=r, column=0, sticky="w", pady=(10, 2), padx=10
        )
        r += 1
        ttk.Entry(f, textvariable=self.file_path, width=55).grid(row=r, column=0, sticky="we", padx=10)
        ttk.Button(f, text="Browse", command=self._browse_file).grid(row=r, column=1, padx=5)
        r += 1

        ttk.Label(f, text="Column name (default 'email'):").grid(row=r, column=0, sticky="w", padx=10)
        r += 1
        ttk.Entry(f, textvariable=self.column_name, width=30).grid(row=r, column=0, sticky="w", padx=10)
        r += 1

        ttk.Label(f, text="Subject:", font=("Segoe UI", 10, "bold")).grid(
            row=r, column=0, sticky="w", pady=(15, 2), padx=10
        )
        r += 1
        ttk.Entry(f, textvariable=self.subject, width=60).grid(row=r, column=0, columnspan=2, sticky="we", padx=10)
        r += 1

        ttk.Label(f, text="Message body:", font=("Segoe UI", 10, "bold")).grid(
            row=r, column=0, sticky="w", pady=(15, 2), padx=10
        )
        r += 1
        ttk.Entry(f, textvariable=self.body_text, width=60).grid(row=r, column=0, columnspan=2, sticky="we", padx=10)
        r += 1
        ttk.Label(f, text="OR load from .txt / .html file:").grid(row=r, column=0, sticky="w", padx=10)
        r += 1
        ttk.Entry(f, textvariable=self.body_file_path, width=55).grid(row=r, column=0, sticky="we", padx=10)
        ttk.Button(f, text="Browse", command=self._browse_body).grid(row=r, column=1, padx=5)
        r += 1

        ttk.Label(f, text="Attachments:", font=("Segoe UI", 10, "bold")).grid(
            row=r, column=0, sticky="w", pady=(15, 2), padx=10
        )
        r += 1
        af = ttk.Frame(f)
        af.grid(row=r, column=0, columnspan=2, sticky="we", padx=10)
        self.attach_list = tk.Listbox(af, height=3, width=60)
        self.attach_list.pack(side="left", fill="both", expand=True)
        ttk.Button(af, text="Add", command=self._add_attach).pack(side="left", padx=5)
        ttk.Button(af, text="Remove", command=self._remove_attach).pack(side="left")
        r += 1

        ttk.Label(f, text="SMTP Accounts (email:password:server:port)", font=("Segoe UI", 10, "bold")).grid(
            row=r, column=0, sticky="w", pady=(15, 2), padx=10
        )
        r += 1
        ttk.Label(f, text="Example: user@gmail.com:abcd efgh ijkl mnop:smtp.gmail.com:587", foreground="gray").grid(
            row=r, column=0, sticky="w", padx=10
        )
        r += 1
        self.accounts_text = scrolledtext.ScrolledText(f, height=4, width=70)
        self.accounts_text.grid(row=r, column=0, columnspan=2, sticky="we", padx=10)
        r += 1

        rot = ttk.Frame(f)
        rot.grid(row=r, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        ttk.Label(rot, text="Rotation:").pack(side="left")
        ttk.Radiobutton(rot, text="Sequential", variable=self.rotation_mode, value="round_robin").pack(side="left", padx=5)
        ttk.Radiobutton(rot, text="Random", variable=self.rotation_mode, value="random").pack(side="left", padx=5)
        r += 1

        ttk.Label(f, text="Options", font=("Segoe UI", 10, "bold")).grid(
            row=r, column=0, sticky="w", pady=(20, 5), padx=10
        )
        r += 1
        ttk.Label(f, text="Min delay (s):").grid(row=r, column=0, sticky="w", padx=10)
        ttk.Spinbox(f, from_=0, to=3600, textvariable=self.delay_min, width=10).grid(
            row=r, column=0, sticky="w", padx=(120, 0)
        )
        r += 1
        ttk.Label(f, text="Max delay (s):").grid(row=r, column=0, sticky="w", padx=10)
        ttk.Spinbox(f, from_=0, to=3600, textvariable=self.delay_max, width=10).grid(
            row=r, column=0, sticky="w", padx=(120, 0)
        )
        r += 1
        ttk.Checkbutton(f, text="Shuffle recipients", variable=self.shuffle_var).grid(row=r, column=0, sticky="w", padx=10)
        ttk.Checkbutton(f, text="HTML content", variable=self.html_var).grid(row=r, column=1, sticky="w")
        r += 1
        ttk.Checkbutton(f, text="Dry Run (simulation)", variable=self.dry_run_var).grid(row=r, column=0, sticky="w", padx=10)
        ttk.Checkbutton(f, text="Resume (skip already sent)", variable=self.resume_var).grid(row=r, column=1, sticky="w")
        r += 1

        bf = ttk.Frame(f)
        bf.grid(row=r, column=0, columnspan=2, pady=20)
        self.btn_start = ttk.Button(bf, text="Start", command=self._start)
        self.btn_start.pack(side="left", padx=5)
        ttk.Button(bf, text="Stop", command=self._stop).pack(side="left", padx=5)
        r += 1

        ttk.Label(f, text="Logs:", font=("Segoe UI", 10, "bold")).grid(
            row=r, column=0, sticky="w", pady=(15, 5), padx=10
        )
        r += 1
        self.log_box = scrolledtext.ScrolledText(f, height=12, state="disabled", wrap=tk.WORD)
        self.log_box.grid(row=r, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        r += 1

        self.progress = ttk.Progressbar(f, orient="horizontal", length=500, mode="determinate")
        self.progress.grid(row=r, column=0, columnspan=2, sticky="we", padx=10, pady=(0, 10))

        f.columnconfigure(0, weight=1)
        self.log("Ready. Load a file and click Start.")

    def _auto_detect_html(self, *args):
        path = self.body_file_path.get().strip().lower()
        if not path:
            return
        if path.endswith((".html", ".htm")):
            self.html_var.set(True)
            self.log("HTML file detected — HTML mode enabled.")
        elif path.endswith(".txt"):
            self.html_var.set(False)
            self.log("Text file detected — Plain text mode enabled.")

    def log(self, message: str):
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, f"{message}\n")
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")

    def _log_async(self, message: str):
        self.after(0, lambda: self.log(message))

    def _set_progress(self, value: int):
        self.after(0, lambda: self.progress.config(value=value))

    def _finish_async(self, message: str | None = None):
        self.after(0, lambda: self._finish(message))

    def _browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV/Excel", "*.csv *.xlsx *.xls")])
        if path:
            self.file_path.set(path)

    def _browse_body(self):
        path = filedialog.askopenfilename(filetypes=[("Text/HTML", "*.txt *.html *.htm")])
        if path:
            self.body_file_path.set(path)

    def _add_attach(self):
        files = filedialog.askopenfilenames(title="Select attachments")
        count = 0
        for f in files:
            if f not in self.attachments:
                self.attachments.append(f)
                self.attach_list.insert(tk.END, Path(f).name)
                count += 1
        if count:
            self.log(f"Added {count} attachment(s).")

    def _remove_attach(self):
        selection = self.attach_list.curselection()
        if selection:
            idx = selection[0]
            self.attach_list.delete(idx)
            del self.attachments[idx]
            self.log("Attachment removed.")

    def _get_body(self) -> str | None:
        if self.body_file_path.get().strip():
            try:
                with open(self.body_file_path.get(), "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as exc:
                self.log(f"Error reading body file: {exc}")
                return None
        return self.body_text.get().strip()

    def _parse_accounts(self) -> list[dict]:
        lines = self.accounts_text.get("1.0", tk.END).strip().splitlines()
        accounts = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) >= 2:
                accounts.append({
                    "user": parts[0].strip(),
                    "password": parts[1].strip(),
                    "server": parts[2].strip() if len(parts) > 2 else "smtp.gmail.com",
                    "port": int(parts[3].strip()) if len(parts) > 3 else 587,
                })
        return accounts

    def _load_sent(self) -> set[str]:
        if Path(self.sent_file).exists():
            try:
                with open(self.sent_file, "r", encoding="utf-8") as f:
                    return set(json.load(f).get("sent", []))
            except Exception:
                return set()
        return set()

    def _save_sent(self, sent_set: set[str]):
        try:
            with open(self.sent_file, "w", encoding="utf-8") as f:
                json.dump({"sent": list(sent_set)}, f, indent=2)
        except Exception as exc:
            self._log_async(f"Error saving sent list: {exc}")

    def _load_account_from_config(self):
        email = ConfigManager.get_email()
        password = CredentialManager.get_password()
        if email and password:
            line = f"{email}:{password}:smtp.gmail.com:587"
            self.accounts_text.insert(tk.END, line + "\n")
            self.log(f"Loaded account from config: {email}")

    def _start(self):
        if self.is_running:
            return
        if not self.file_path.get():
            messagebox.showerror("Error", "Select an email file.")
            return
        if not self.subject.get().strip():
            messagebox.showerror("Error", "Enter a subject.")
            return
        body = self._get_body()
        if not body:
            messagebox.showerror("Error", "Enter a message body or load a file.")
            return

        accounts = self._parse_accounts()
        if not accounts:
            messagebox.showerror("Error", "No SMTP accounts configured.\nAdd accounts or run setup.")
            return

        self.is_running = True
        self.stop_requested = False
        self.btn_start.config(state="disabled", text="Running...")
        self._set_progress(0)
        self.log("Starting send process...")

        thread = threading.Thread(target=self._run, args=(accounts, body), daemon=True)
        thread.start()

    def _stop(self):
        if self.is_running:
            self.stop_requested = True
            self.log("Stop requested. Finishing current email...")

    def _finish(self, message: str | None = None):
        self.is_running = False
        self.btn_start.config(state="normal", text="Start")
        if message:
            self.log(message)
        self.log("Ready for new send.")

    def _run(self, accounts: list[dict], body: str):
        try:
            emails = load_emails(self.file_path.get(), self.column_name.get() or None)
            if not emails:
                self._finish_async("No emails loaded.")
                return

            sent = set()
            if self.resume_var.get():
                sent = self._load_sent()
                emails = [e for e in emails if e not in sent]
                self._log_async(f"Resume: {len(sent)} already sent, {len(emails)} remaining.")

            if not emails:
                self._finish_async("All emails already sent.")
                return

            if self.shuffle_var.get():
                random.shuffle(emails)

            total = len(emails)
            service = EmailService(accounts, self.rotation_mode.get())
            success = 0
            failed = 0

            for idx, email in enumerate(emails):
                if self.stop_requested:
                    self._log_async("Interrupted by user.")
                    break

                ok = service.send(
                    email,
                    self.subject.get(),
                    body,
                    self.html_var.get(),
                    self.attachments,
                    self.dry_run_var.get(),
                )
                if ok:
                    success += 1
                    if not self.dry_run_var.get():
                        sent.add(email)
                        self._save_sent(sent)
                else:
                    failed += 1

                progress = int(((idx + 1) / total) * 100)
                self._set_progress(progress)

                if idx < total - 1 and not self.dry_run_var.get() and not self.stop_requested:
                    delay = random.randint(self.delay_min.get(), self.delay_max.get())
                    self._log_async(f"Waiting {delay}s before next send...")
                    time.sleep(delay)

            self._log_async(f"Finished. Success: {success}, Failed: {failed}")
        except Exception as exc:
            self._log_async(f"Critical error: {exc}")
        finally:
            self._finish_async()