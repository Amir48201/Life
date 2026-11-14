import os
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

        self.data = self.load_data()
        self.selected_week_idx = 0
        self.zoom_factor = 1.0  # ضریب زوم (1.0 = پر کردن کامل عرض صفحه)
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
        # بخش چپ: نوار کنترل زوم + بوم اسکرول‌پذیر شبکه
        left_frame = tk.Frame(self.tab_overview, bg=BG_PANEL)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # نوار ابزار زوم در بالای جدول
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

        # ناحیه Canvas همراه با Scrollbar عمودی و افقی
        canvas_holder = tk.Frame(left_frame, bg=BG_PANEL)
        canvas_holder.pack(fill="both", expand=True)

        self.v_scroll = tk.Scrollbar(canvas_holder, orient="vertical")
        self.h_scroll = tk.Scrollbar(canvas_holder, orient="horizontal")

        self.canvas = tk.Canvas(
            canvas_holder,
            bg=BG_PANEL,
            highlightthickness=0,
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set,
        )

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.bind("<Configure>", lambda e: self.draw_life_grid())
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Control-MouseWheel>", self._on_ctrl_wheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_wheel)

        # بخش راست: پنل ویرایش و یادداشت هفته انتخاب‌شده
        right_panel = tk.Frame(self.tab_overview, bg=BG_PANEL, width=340)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        self.ov_week_title = tk.Label(
            right_panel, text="Week #1", font=("Segoe UI", 13, "bold"), bg=BG_PANEL, fg=ACCENT_GOLD
        )
        self.ov_week_title.pack(anchor="w", padx=18, pady=(18, 2))

        self.ov_week_dates = tk.Label(
            right_panel, text="", font=("Segoe UI", 9), bg=BG_PANEL, fg=TEXT_MUTED
        )
        self.ov_week_dates.pack(anchor="w", padx=18, pady=(0, 14))

        tk.Label(
            right_panel, text="Category / Color Tag:", font=("Segoe UI", 10, "bold"), bg=BG_PANEL, fg=TEXT_PRIMARY
        ).pack(anchor="w", padx=18, pady=(4, 6))

        self.cat_var = tk.StringVar()
        self.cat_dropdown = ttk.Combobox(
            right_panel, textvariable=self.cat_var, state="readonly", font=("Segoe UI", 10)
        )
        self.cat_dropdown.pack(fill="x", padx=18, pady=(0, 14))
        self.refresh_category_dropdown()

        tk.Label(
            right_panel, text="Weekly Note & Reflection:", font=("Segoe UI", 10, "bold"), bg=BG_PANEL, fg=TEXT_PRIMARY
        ).pack(anchor="w", padx=18, pady=(4, 6))

        self.ov_note_text = tk.Text(
            right_panel,
            font=("Segoe UI", 10),
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            wrap="word",
            height=12,
            padx=10,
            pady=10,
        )
        self.ov_note_text.pack(fill="x", padx=18, pady=(0, 14))

        tk.Button(
            right_panel,
            text="Save Week Note & Color",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_GREEN,
            fg="#FFFFFF",
            relief="flat",
            cursor="hand2",
            command=self.save_overview_week_details,
        ).pack(fill="x", padx=18, ipady=6, pady=(0, 8))

        tk.Button(
            right_panel,
            text="Open Daily View for This Week →",
            font=("Segoe UI", 9, "bold"),
            bg=BG_CARD,
            fg=ACCENT_GOLD,
            relief="flat",
            cursor="hand2",
            command=lambda: self.notebook.select(self.tab_week),
        ).pack(fill="x", padx=18, ipady=6)

        self.legend_frame = tk.Frame(right_panel, bg=BG_PANEL)
        self.legend_frame.pack(side="bottom", fill="x", padx=18, pady=16)
        self.render_legend()

    def _on_mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_shift_wheel(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_ctrl_wheel(self, event):
        if event.delta > 0:
            self.change_zoom(0.15)
        else:
            self.change_zoom(-0.15)

    def change_zoom(self, delta: float):
        self.zoom_factor = round(max(0.4, min(2.5, self.zoom_factor + delta)), 2)
        self.zoom_label.config(text=f"{int(self.zoom_factor * 100)}%")
        self.draw_life_grid()

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.zoom_label.config(text="100%")
        self.draw_life_grid()

    def scroll_to_current_week(self):
        curr_week = self.get_current_week_index()
        curr_
