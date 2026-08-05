"""Main email sender GUI dashboard — listbox attachments + tooltips."""
import logging
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path

from emailsenderpro.config_editor import ConfigEditor
from emailsenderpro.core.config_manager import ConfigManager
from emailsenderpro.core.credential_manager import CredentialManager
from emailsenderpro.core.email_service import EmailService
from emailsenderpro.services.excel_service import load_emails

logger = logging.getLogger(__name__)


class Dashboard(tk.Tk):
    """Main application dashboard with listbox attachments and help tooltips."""

    def __init__(self):
        super().__init__()
        self.title("EmailSenderPro - Dashboard")
        self.geometry("1100x780")
        self.minsize(1000, 700)

        self.config_manager = ConfigManager()
        self.credential_manager = CredentialManager()
        self.sending_thread = None
        self.stop_event = threading.Event()

        self._build_ui()
        self._load_defaults()
        self._load_smtp_auto()
        self._check_first_run()

    def _build_ui(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        # ========== LEFT COLUMN ==========
        left = tk.Frame(self, padx=15, pady=10)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)

        # Header
        tk.Label(
            left,
            text="EmailSenderPro Dashboard",
            font=("Segoe UI", 17, "bold"),
            fg="#2c3e50",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Recipients
        r_frame = tk.LabelFrame(left, text="Recipients", font=("Segoe UI", 9, "bold"), padx=8, pady=5)
        r_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        r_frame.columnconfigure(0, weight=1)

        self.recipient_path = tk.StringVar()
        tk.Entry(r_frame, textvariable=self.recipient_path, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="ew", ipady=2)
        tk.Button(r_frame, text="Browse", command=self._browse_recipients, width=8).grid(row=0, column=1, padx=(5, 0))

        # Message
        m_frame = tk.LabelFrame(left, text="Message", font=("Segoe UI", 9, "bold"), padx=8, pady=6)
        m_frame.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        m_frame.columnconfigure(1, weight=1)

        # Subject
        tk.Label(m_frame, text="Subject:", font=("Segoe UI", 9), anchor="w").grid(row=0, column=0, sticky="w")
        self.subject_var = tk.StringVar()
        tk.Entry(m_frame, textvariable=self.subject_var, font=("Segoe UI", 9)).grid(row=0, column=1, sticky="ew", ipady=2, pady=(0, 4))

        # Body file
        tk.Label(m_frame, text="Body file:", font=("Segoe UI", 9), anchor="w").grid(row=1, column=0, sticky="w")
        bf = tk.Frame(m_frame)
        bf.grid(row=1, column=1, sticky="ew", pady=(0, 4))
        bf.columnconfigure(0, weight=1)
        self.body_file_path = tk.StringVar()
        self.body_file_path.trace_add("write", self._auto_detect_html)
        tk.Entry(bf, textvariable=self.body_file_path, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="ew", ipady=2)
        tk.Button(bf, text="Browse", command=self._browse_body, width=8).grid(row=0, column=1, padx=(5, 0))

        # Body text
        tk.Label(m_frame, text="Or type / edit body here:", font=("Segoe UI", 8), fg="#7f8c8d", anchor="w").grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 2))
        self.body_text = scrolledtext.ScrolledText(
            m_frame, height=6, font=("Segoe UI", 10), wrap=tk.WORD, relief=tk.SUNKEN, bd=1
        )
        self.body_text.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        # Attachments — LISTBOX STYLE
        a_frame = tk.LabelFrame(left, text="Attachments", font=("Segoe UI", 9, "bold"), padx=8, pady=5)
        a_frame.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        a_frame.columnconfigure(0, weight=1)

        self.attachments_list = tk.Listbox(a_frame, height=3, font=("Segoe UI", 9), selectmode=tk.SINGLE)
        self.attachments_list.grid(row=0, column=0, rowspan=2, sticky="nsew", pady=(0, 4))

        ab = tk.Frame(a_frame)
        ab.grid(row=0, column=1, sticky="n", padx=(8, 0))
        tk.Button(ab, text="Add", command=self._add_attachment, width=8).pack(pady=(0, 4))
        tk.Button(ab, text="Remove", command=self._remove_attachment, width=8).pack()

        # SMTP Accounts
        s_frame = tk.LabelFrame(left, text="SMTP Accounts", font=("Segoe UI", 9, "bold"), padx=8, pady=5)
        s_frame.grid(row=4, column=0, sticky="ew", pady=(0, 6))
        s_frame.columnconfigure(0, weight=1)

        tk.Label(s_frame, text="Format: email:password:server:port", font=("Segoe UI", 8), fg="#7f8c8d").grid(row=0, column=0, columnspan=3, sticky="w")
        self.smtp_text = scrolledtext.ScrolledText(s_frame, height=3, font=("Consolas", 9))
        self.smtp_text.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 4))

        sb = tk.Frame(s_frame)
        sb.grid(row=2, column=0, columnspan=3, sticky="w")
        tk.Button(sb, text="Load from Config", command=self._load_from_config, width=13).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(sb, text="Clear", command=lambda: self.smtp_text.delete("1.0", tk.END), width=8).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(sb, text="Edit Config", command=self._open_config_editor, width=10).pack(side=tk.LEFT)

        # Options
        o_frame = tk.LabelFrame(left, text="Options", font=("Segoe UI", 9, "bold"), padx=8, pady=5)
        o_frame.grid(row=5, column=0, sticky="ew", pady=(0, 4))

        # Delays
        df = tk.Frame(o_frame)
        df.pack(fill=tk.X, pady=(0, 4))
        tk.Label(df, text="Min delay (s):", font=("Segoe UI", 9), width=11, anchor="w").pack(side=tk.LEFT)
        self.min_delay_var = tk.StringVar(value="300")
        tk.Entry(df, textvariable=self.min_delay_var, width=7, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 12))
        tk.Label(df, text="Max delay (s):", font=("Segoe UI", 9), width=11, anchor="w").pack(side=tk.LEFT)
        self.max_delay_var = tk.StringVar(value="600")
        tk.Entry(df, textvariable=self.max_delay_var, width=7, font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # Checkboxes with tooltips
        cf = tk.Frame(o_frame)
        cf.pack(fill=tk.X, pady=(3, 0))

        self.html_var = tk.BooleanVar(value=False)
        tk.Checkbutton(cf, text="HTML", variable=self.html_var, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8))

        self.dry_run_var = tk.BooleanVar(value=True)
        tk.Checkbutton(cf, text="Dry Run", variable=self.dry_run_var, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8))

        self.resume_var = tk.BooleanVar(value=True)
        tk.Checkbutton(cf, text="Resume", variable=self.resume_var, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8))

        self.shuffle_var = tk.BooleanVar(value=False)
        tk.Checkbutton(cf, text="Shuffle", variable=self.shuffle_var, font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # Tooltips row
        tf = tk.Frame(o_frame)
        tf.pack(fill=tk.X, pady=(2, 0))
        tk.Label(tf, text="HTML = formatted email (bold, colors, links)", font=("Segoe UI", 7), fg="#95a5a6").pack(side=tk.LEFT, padx=(0, 12))
        tk.Label(tf, text="Dry Run = simulate sending without real delivery", font=("Segoe UI", 7), fg="#95a5a6").pack(side=tk.LEFT, padx=(0, 12))
        tk.Label(tf, text="Resume = skip emails already sent (saved in sent.json)", font=("Segoe UI", 7), fg="#95a5a6").pack(side=tk.LEFT, padx=(0, 12))
        tk.Label(tf, text="Shuffle = randomize recipient order", font=("Segoe UI", 7), fg="#95a5a6").pack(side=tk.LEFT)

        # ========== RIGHT COLUMN ==========
        right = tk.Frame(self, padx=10, pady=10)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        # Progress
        p_frame = tk.LabelFrame(right, text="Progress", font=("Segoe UI", 9, "bold"), padx=10, pady=8)
        p_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        p_frame.columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(p_frame, variable=self.progress_var, maximum=100).grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.progress_label = tk.Label(p_frame, text="Ready — 0 / 0 emails", font=("Segoe UI", 9), fg="#7f8c8d")
        self.progress_label.grid(row=1, column=0, sticky="w")
        tk.Label(p_frame, text="Green = sent | Grey = remaining | Blue = current", font=("Segoe UI", 8), fg="#95a5a6").grid(row=2, column=0, sticky="w", pady=(2, 0))

        # Logs
        l_frame = tk.LabelFrame(right, text="Logs", font=("Segoe UI", 9, "bold"), padx=10, pady=8)
        l_frame.grid(row=1, column=0, sticky="nsew")
        l_frame.rowconfigure(0, weight=1)
        l_frame.columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            l_frame, height=18, font=("Consolas", 9), state=tk.DISABLED, wrap=tk.WORD
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # ========== BOTTOM ACTION BAR ==========
        bottom = tk.Frame(self, padx=15, pady=12, bg="#ecf0f1")
        bottom.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.start_btn = tk.Button(
            bottom,
            text="▶  Start",
            command=self._on_start,
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            width=16,
            cursor="hand2",
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 12))

        self.stop_btn = tk.Button(
            bottom,
            text="⏹  Stop",
            command=self._on_stop,
            bg="#e74c3c",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            width=16,
            state=tk.DISABLED,
            cursor="hand2",
        )
        self.stop_btn.pack(side=tk.LEFT)

    def _load_defaults(self):
        examples_dir = Path(__file__).parent.parent.parent / "examples"
        default_emails = examples_dir / "emails.example.csv"
        if default_emails.exists():
            self.recipient_path.set(str(default_emails))
            self._log(f"Default recipients: {default_emails.name}")

        default_body = examples_dir / "body.txt"
        if default_body.exists():
            self.body_file_path.set(str(default_body))
            try:
                with open(default_body, "r", encoding="utf-8") as f:
                    content = f.read()
                self.body_text.delete("1.0", tk.END)
                self.body_text.insert(tk.END, content)
                self._log(f"Default body: {default_body.name}")
            except Exception as e:
                self._log(f"Error loading default body: {e}", "error")

    def _load_smtp_auto(self):
        email = self.config_manager.get("email", "")
        if not email:
            return
        password = self.credential_manager.get_password(email) or ""
        if not password:
            return
        server = self.config_manager.get("server", "smtp.gmail.com")
        port = self.config_manager.get("port", 587)
        account_str = f"{email}:{password}:{server}:{port}"
        self.smtp_text.delete("1.0", tk.END)
        self.smtp_text.insert(tk.END, account_str)
        self._log(f"Auto-loaded SMTP: {email}")

    def _check_first_run(self):
        if not self.config_manager.has_config():
            self.withdraw()
            from emailsenderpro.setup_wizard import SetupWizard
            SetupWizard(self, on_complete=self.deiconify)

    def _browse_recipients(self):
        path = filedialog.askopenfilename(
            title="Select Recipients File",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )
        if path:
            self.recipient_path.set(path)
            self._log(f"Selected recipients: {path}")

    def _browse_body(self):
        path = filedialog.askopenfilename(
            title="Select Body File",
            filetypes=[
                ("Text & HTML files", "*.txt *.html *.htm"),
                ("Text files", "*.txt"),
                ("HTML files", "*.html *.htm"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.body_file_path.set(path)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.body_text.delete("1.0", tk.END)
                self.body_text.insert(tk.END, content)
                self._log(f"Loaded body: {path}")
            except Exception as e:
                self._log(f"Error reading body: {e}", "error")

    def _auto_detect_html(self, *args):
        path = self.body_file_path.get().strip().lower()
        if path.endswith((".html", ".htm")):
            self.html_var.set(True)
            self._log("HTML mode enabled.")
        elif path.endswith(".txt"):
            self.html_var.set(False)
            self._log("Plain text mode enabled.")

    def _add_attachment(self):
        paths = filedialog.askopenfilenames(title="Select Attachments")
        for p in paths:
            if p and p not in self.attachments_list.get(0, tk.END):
                self.attachments_list.insert(tk.END, p)
        count = self.attachments_list.size()
        if paths:
            self._log(f"Attachments: {count} file(s)")

    def _remove_attachment(self):
        sel = self.attachments_list.curselection()
        if sel:
            self.attachments_list.delete(sel[0])
            self._log(f"Removed attachment. Remaining: {self.attachments_list.size()}")
        else:
            messagebox.showinfo("Select First", "Click on a file in the list to select it, then click Remove.")

    def _load_from_config(self):
        email = self.config_manager.get("email", "")
        if not email:
            messagebox.showinfo("No Config", "No saved configuration found.")
            return
        password = self.credential_manager.get_password(email) or ""
        server = self.config_manager.get("server", "smtp.gmail.com")
        port = self.config_manager.get("port", 587)
        account_str = f"{email}:{password}:{server}:{port}"
        self.smtp_text.delete("1.0", tk.END)
        self.smtp_text.insert(tk.END, account_str)
        self._log(f"Loaded account: {email}")

    def _open_config_editor(self):
        ConfigEditor(self, on_save=self._load_from_config)

    def _log(self, message, level="info"):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        logger.log(getattr(logging, level.upper(), logging.INFO), message)

    def _on_progress(self, current: int, total: int) -> None:
        if total > 0:
            pct = (current / total) * 100
            self.progress_var.set(pct)
            self.progress_label.config(text=f"Sending... {current} / {total} ({pct:.0f}%)", fg="#3498db")
        else:
            self.progress_label.config(text="Ready", fg="#7f8c8d")

    def _on_start(self):
        if self.sending_thread and self.sending_thread.is_alive():
            messagebox.showwarning("Busy", "A sending operation is already in progress.")
            return

        recipient_file = self.recipient_path.get().strip()
        if not recipient_file:
            messagebox.showwarning("Missing File", "Please select a recipients file.")
            return

        subject = self.subject_var.get().strip()
        if not subject:
            messagebox.showwarning("Missing Subject", "Please enter an email subject.")
            return

        body = self.body_text.get("1.0", tk.END).strip()
        if not body:
            messagebox.showwarning("Missing Body", "Please enter an email body.")
            return

        accounts_raw = self.smtp_text.get("1.0", tk.END).strip()
        if not accounts_raw:
            messagebox.showwarning("Missing Accounts", "Please enter at least one SMTP account.")
            return

        accounts = [line.strip() for line in accounts_raw.splitlines() if line.strip()]

        try:
            min_delay = int(self.min_delay_var.get())
            max_delay = int(self.max_delay_var.get())
        except ValueError:
            messagebox.showwarning("Invalid Delay", "Delay values must be integers.")
            return

        try:
            recipients = load_emails(recipient_file)
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load recipients: {e}")
            return

        if not recipients:
            messagebox.showwarning("No Recipients", "The file contains no valid email addresses.")
            return

        # Collect attachments from listbox
        attachments = []
        for i in range(self.attachments_list.size()):
            p = self.attachments_list.get(i)
            if os.path.exists(p):
                attachments.append(p)

        self.stop_event.clear()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.progress_label.config(text=f"0 / {len(recipients)} emails", fg="#3498db")

        service = EmailService(
            accounts=accounts, subject=subject, body=body,
            is_html=self.html_var.get(), attachments=attachments,
            min_delay=min_delay, max_delay=max_delay,
            dry_run=self.dry_run_var.get(), resume=self.resume_var.get(),
            shuffle=self.shuffle_var.get(), stop_event=self.stop_event,
        )
        service.set_log_callback(lambda msg: self.after(0, self._log, msg))
        service.set_progress_callback(lambda c, t: self.after(0, self._on_progress, c, t))

        self.sending_thread = threading.Thread(target=self._send_worker, args=(service, recipients), daemon=True)
        self.sending_thread.start()

    def _send_worker(self, service, recipients):
        try:
            stats = service.send_bulk(recipients)
            self.after(0, self._on_send_complete, stats)
        except Exception as e:
            self.after(0, self._log, f"Unexpected error: {e}", "error")
            self.after(0, self._reset_ui)

    def _on_send_complete(self, stats):
        self._reset_ui()
        mode = "Dry Run" if self.dry_run_var.get() else "Send"
        status = " (stopped)" if stats.get("stopped") else ""
        self._log(f"{mode} complete{status}! Sent: {stats['sent']}, Skipped: {stats['skipped']}, Failed: {stats['failed']}")
        messagebox.showinfo("Complete", f"Sent: {stats['sent']}\nSkipped: {stats['skipped']}\nFailed: {stats['failed']}")

    def _on_stop(self):
        self.stop_event.set()
        self._log("Stop requested. Aborting after current email...")
        self.stop_btn.config(state=tk.DISABLED)

    def _reset_ui(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_var.set(100 if self.progress_var.get() > 0 else 0)
        self.progress_label.config(text="Ready — 0 / 0 emails", fg="#7f8c8d")
