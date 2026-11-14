import os
import sys
import json
import calendar
import traceback
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from datetime import date, timedelta

DATA_FILE = os.path.join(os.path.expanduser("~"), ".life_in_weeks_data.json")

BG_MAIN = "#121318"
BG_PANEL = "#1A1C24"
BG_CARD = "#222530"
BORDER_COLOR = "#343846"
TEXT_PRIMARY = "#ECEEF4"
TEXT_MUTED = "#8E95A8"
ACCENT_GOLD = "#FFC107"
ACCENT_GREEN = "#4CAF50"
FUTURE_BOX = "#252834"


def resource_path(relative_path: str) -> str:
    """پیدا کردن مسیر فایل‌های داخلی برنامه (مثل آیکون)"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    candidate = os.path.join(base_dir, relative_path)
    if os.path.exists(candidate):
        return candidate
    return os.path.join(os.path.abspath("."), relative_path)


def get_anniversary(birth_date: date, years_to_add: int) -> date:
    """محاسبه دقیق تاریخ سالگرد تولد با پشتیبانی از سال‌های کبیسه"""
    target_year = birth_date.year + years_to_add
    max_day = calendar.monthrange(target_year, birth_date.month)[1]
    return date(target_year, birth_date.month, min(birth_date.day, max_day))


class LifeApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Life")
        self.root.geometry("1280x820")
        self.root.minsize(1050, 700)
        self.root.configure(bg=BG_MAIN)

        try:
            ico_path = resource_path("yin_yang.ico")
            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
        except Exception:
            pass

        self.data = self.load_data()
        self.selected_week_idx = 0
        self.zoom_factor = 1.0
        self.initial_scroll_done = False

        self.setup_styles()

        if not self.data.get("birth_date"):
            self.show_setup_dialog(first_time=True)
        else:
            self.init_main_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=BG_PANEL,
            foreground=TEXT_MUTED,
            padding=[18, 8],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", BG_CARD)],
            foreground=[("selected", ACCENT_GOLD)],
        )

    def load_data(self) -> dict:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "birth_date": None,
            "target_age": 80,
            "categories": {
                "Default Past": "#4CAF50",
                "Work & Research": "#2196F3",
                "Learning & Growth": "#9C27B0",
                "Milestone": "#FF5722",
                "Rest & Travel": "#00BCD4",
            },
            "weeks": {},
        }

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_current_week_index(self) -> int:
        b_date = date.fromisoformat(self.data["birth_date"])
        today = date.today()
        if today <= b_date:
            return 0

        age = today.year - b_date.year
        if (today.month, today.day) < (b_date.month, b_date.day):
            age -= 1
        age = max(0, age)

        last_bday = get_anniversary(b_date, age)
        days_since_bday = (today - last_bday).days
        week_in_year = min(51, days_since_bday // 7)
        return (age * 52) + week_in_year

    def get_week_date_range(self, week_idx: int):
        b_date = date.fromisoformat(self.data["birth_date"])
        age_yr = week_idx // 52
        wk_of_yr = week_idx % 52

        year_start = get_anniversary(b_date, age_yr)
        next_year_start = get_anniversary(b_date, age_yr + 1)

        w_start = year_start + timedelta(days=wk_of_yr * 7)
        if wk_of_yr == 51:
            w_end = next_year_start - timedelta(days=1)
        else:
            w_end = w_start + timedelta(days=6)

        return w_start, w_end

    def show_setup_dialog(self, first_time=False):
        dialog = tk.Toplevel(self.root)
        dialog.title("Welcome to Life — Setup")
        dialog.geometry("420x340")
        dialog.configure(bg=BG_PANEL)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        if first_time:
            dialog.protocol("WM_DELETE_WINDOW", self.root.destroy)

        tk.Label(
            dialog, text="Life in Weeks", font=("Segoe UI", 18, "bold"), bg=BG_PANEL, fg=ACCENT_GOLD
        ).pack(pady=(22, 5))

        tk.Label(
            dialog,
            text="Enter your birth date and target lifespan to generate your grid.",
            font=("Segoe UI", 9),
            bg=BG_PANEL,
            fg=TEXT_MUTED,
        ).pack(pady=(0, 20))

        form = tk.Frame(dialog, bg=BG_PANEL)
        form.pack(padx=35, fill="x")

        tk.Label(
            form, text="Birth Date (YYYY-MM-DD):", font=("Segoe UI", 10), bg=BG_PANEL, fg=TEXT_PRIMARY
        ).pack(anchor="w")
        birth_entry = tk.Entry(
            form, font=("Segoe UI", 11), bg=BG_CARD, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat"
        )
        birth_entry.pack(fill="x", pady=(4, 14), ipady=5)
        birth_entry.insert(0, self.data.get("birth_date") or "2001-12-15")

        tk.Label(
            form, text="Target Age (Years):", font=("Segoe UI", 10), bg=BG_PANEL, fg=TEXT_PRIMARY
        ).pack(anchor="w")
        age_entry = tk.Entry(
            form, font=("Segoe UI", 11), bg=BG_CARD, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat"
        )
        age_entry.pack(fill="x", pady=(4, 20), ipady=5)
        age_entry.insert(0, str(self.data.get("target_age", 80)))

        def on_save():
            b_str = birth_entry.get().strip()
            a_str = age_entry.get().strip()
            try:
                b_dt = date.fromisoformat(b_str)
                if b_dt > date.today():
                    raise ValueError("Birth date cannot be in the future.")
                age_val = int(a_str)
                if not (10 <= age_val <= 120):
                    raise ValueError("Target age must be between 10 and 120.")
            except Exception as e:
                messagebox.showerror("Invalid Input", f"Please check your inputs:\n{e}", parent=dialog)
                return

            self.data["birth_date"] = b_dt.isoformat()
            self.data["target_age"] = age_val
            self.save_data()
            dialog.destroy()

            self.initial_scroll_done = False
            for widget in self.root.winfo_children():
                widget.destroy()
            self.init_main_ui()

        tk.Button(
            form,
            text="Generate My Life Grid",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_GOLD,
            fg="#121318",
            activebackground="#FFD54F",
            relief="flat",
            cursor="hand2",
            command=on_save,
        ).pack(fill="x", ipady=7)

    def init_main_ui(self):
        self.selected_week_idx = self.get_current_week_index()

        header = tk.Frame(self.root, bg=BG_PANEL, height=54)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(
            header, text="LIFE", font=("Segoe UI", 15, "bold"), bg=BG_PANEL, fg=ACCENT_GOLD
        ).pack(side="left", padx=(20, 12))

        self.stats_label = tk.Label(
            header, text="", font=("Segoe UI", 10), bg=BG_PANEL, fg=TEXT_PRIMARY
        )
        self.stats_label.pack(side="left", padx=10)

        tk.Button(
            header,
            text="⚙ Settings",
            font=("Segoe UI", 9),
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            command=lambda: self.show_setup_dialog(first_time=False),
        ).pack(side="right", padx=16, pady=12)

        tk.Button(
            header,
            text="+ Category",
            font=("Segoe UI", 9),
            bg=BG_CARD,
            fg=ACCENT_GOLD,
            relief="flat",
            cursor="hand2",
            command=self.add_category_dialog,
        ).pack(side="right", padx=4, pady=12)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(8, 12))

        self.tab_overview = tk.Frame(self.notebook, bg=BG_MAIN)
        self.tab_week = tk.Frame(self.notebook, bg=BG_MAIN)

        self.notebook.add(self.tab_overview, text="  Life Overview (All Years)  ")
        self.notebook.add(self.tab_week, text="  Week & Daily Tracker  ")

        self.build_overview_tab()
        self.build_week_tab()
        self.update_header_stats()
        self.load_week_into_panels(self.selected_week_idx)

    def update_header_stats(self):
        curr = self.get_current_week_index()
        total = self.data["target_age"] * 52
        rem = max(0, total - curr)
        pct = min(100.0, (curr / total) * 100) if total > 0 else 0
        age_yr = curr // 52
        wk_yr = (curr % 52) + 1
        self.stats_label.config(
            text=f"Age {age_yr}, Week {wk_yr}/52   •   {pct:.1f}% Lived   •   {rem:,} Weeks Remaining"
        )

    def build_overview_tab(self):
        left_frame = tk.Frame(self.tab_overview, bg=BG_PANEL)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        zoom_bar = tk.Frame(left_frame, bg=BG_CARD, height=38)
        zoom_bar.pack(fill="x", side="top")
        zoom_bar.pack_propagate(False)

        tk.Label(
            zoom_bar,
            text="  Scroll: Mouse Wheel  |  Zoom: Ctrl + Wheel",
            font=("Segoe UI", 8),
            bg=BG_CARD,
            fg=TEXT_MUTED,
        ).pack(side="left", padx=8)

        tk.Button(
            zoom_bar,
            text=" + ",
            font=("Segoe UI", 10, "bold"),
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            command=lambda: self.change_zoom(0.2),
        ).pack(side="right", padx=(2, 10), pady=5)

        self.zoom_label = tk.Label(
            zoom_bar, text="100%", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=ACCENT_GOLD, width=6
        )
        self.zoom_label.pack(side="right", padx=2)

        tk.Button(
            zoom_bar,
            text=" - ",
            font=("Segoe UI", 10, "bold"),
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            command=lambda: self.change_zoom(-0.2),
        ).pack(side="right", padx=2, pady=5)

        tk.Button(
            zoom_bar,
            text="Fit Width",
            font=("Segoe UI", 8, "bold"),
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            command=self.reset_zoom,
        ).pack(side="right", padx=6, pady=5)

        tk.Button(
            zoom_bar,
            text="Jump to Now",
            font=("Segoe UI", 8, "bold"),
            bg=BG_PANEL,
            fg=ACCENT_GOLD,
            relief="flat",
            cursor="hand2",
            command=self.scroll_to_current_week,
        ).pack(side="right", padx=4, pady=5)

        canvas_holder = tk.Frame(left_frame, bg=BG_
