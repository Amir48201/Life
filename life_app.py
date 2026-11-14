import os
import sys
import json
import calendar
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
    """پیدا کردن مسیر فایل‌های داخلی (مثل آیکون) هم در حالت کد و هم داخل فایل EXE"""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def get_anniversary(birth_date: date, years_to_add: int) -> date:
    """محاسبه دقیق تاریخ سالگرد تولد با پشتیبانی از ۲۹ فوریه در سال‌های کبیسه"""
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

        # تنظیم آیکون یین و یانگ برای پنجره برنامه و نوار وظیفه
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
            self.data["target_age"] = age
