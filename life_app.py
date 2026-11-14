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
        curr_row = curr_week // 52
        total_rows = max(1, self.data["target_age"])
        target_fraction = max(0.0, min(1.0, (curr_row - 5) / total_rows))
        self.canvas.yview_moveto(target_fraction)

    def refresh_category_dropdown(self):
        cats = ["(None / Default)"] + list(self.data["categories"].keys())
        self.cat_dropdown["values"] = cats

    def render_legend(self):
        for w in self.legend_frame.winfo_children():
            w.destroy()
        tk.Label(
            self.legend_frame, text="Categories:", font=("Segoe UI", 9, "bold"), bg=BG_PANEL, fg=TEXT_MUTED
        ).pack(anchor="w", pady=(0, 4))
        for name, color in self.data["categories"].items():
            row = tk.Frame(self.legend_frame, bg=BG_PANEL)
            row.pack(anchor="w", pady=1)
            tk.Label(row, text="■", font=("Segoe UI", 11), bg=BG_PANEL, fg=color).pack(side="left")
            tk.Label(row, text=f" {name}", font=("Segoe UI", 9), bg=BG_PANEL, fg=TEXT_PRIMARY).pack(side="left")

    def add_category_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("New Color Category")
        win.geometry("320x200")
        win.configure(bg=BG_PANEL)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="Category Name:", font=("Segoe UI", 10), bg=BG_PANEL, fg=TEXT_PRIMARY).pack(
            anchor="w", padx=20, pady=(18, 4)
        )
        name_ent = tk.Entry(win, font=("Segoe UI", 10), bg=BG_CARD, fg=TEXT_PRIMARY, relief="flat")
        name_ent.pack(fill="x", padx=20, ipady=4)

        chosen_color = ["#E91E63"]

        def pick_color():
            c = colorchooser.askcolor(title="Choose Category Color", parent=win)
            if c and c[1]:
                chosen_color[0] = c[1]
                color_btn.config(bg=c[1])

        color_btn = tk.Button(
            win, text="Pick Color", bg=chosen_color[0], fg="#FFFFFF", relief="flat", command=pick_color
        )
        color_btn.pack(fill="x", padx=20, pady=14, ipady=4)

        def save_cat():
            n = name_ent.get().strip()
            if n:
                self.data["categories"][n] = chosen_color[0]
                self.save_data()
                self.refresh_category_dropdown()
                self.render_legend()
                win.destroy()

        tk.Button(
            win, text="Add Category", bg=ACCENT_GOLD, fg="#121318", font=("Segoe UI", 9, "bold"), relief="flat", command=save_cat
        ).pack(fill="x", padx=20, ipady=5)

    def draw_life_grid(self):
        self.canvas.delete("all")

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            return

        cols = 52
        rows = self.data["target_age"]
        curr_week = self.get_current_week_index()

        pad_left = 42
        pad_right = 20
        pad_top = 28
        pad_bottom = 28

        base_avail_w = max(200, w - (pad_left + pad_right))
        base_pitch = base_avail_w / cols
        pitch = max(6.0, base_pitch * self.zoom_factor)
        box = max(4.0, pitch * 0.74)

        grid_w = cols * pitch
        grid_h = rows * pitch

        total_canvas_w = max(w, grid_w + pad_left + pad_right)
        total_canvas_h = max(h, grid_h + pad_top + pad_bottom)

        start_x = pad_left if (grid_w + pad_left + pad_right) >= w else (w - grid_w) / 2
        start_y = pad_top

        for c in range(cols):
            if c == 0 or (c + 1) % 5 == 0:
                self.canvas.create_text(
                    start_x + c * pitch + box / 2,
                    start_y - 10,
                    text=str(c + 1),
                    fill=TEXT_MUTED,
                    font=("Segoe UI", 8),
                    anchor="s",
                )

        for r in range(rows):
            if pitch >= 11 or r % 5 == 0:
                self.canvas.create_text(
                    start_x - 8,
                    start_y + r * pitch + box / 2,
                    text=str(r),
                    fill=ACCENT_GOLD if r == (curr_week // 52) else TEXT_MUTED,
                    font=("Segoe UI", 8, "bold" if r == (curr_week // 52) else "normal"),
                    anchor="e",
                )

            for c in range(cols):
                idx = r * cols + c
                x0 = start_x + c * pitch
                y0 = start_y + r * pitch
                x1 = x0 + box
                y1 = y0 + box

                w_data = self.data["weeks"].get(str(idx), {})
                cat = w_data.get("category")
                has_note = bool(w_data.get("note", "").strip())

                if cat and cat in self.data["categories"]:
                    fill_color = self.data["categories"][cat]
                elif idx < curr_week:
                    fill_color = ACCENT_GREEN
                elif idx == curr_week:
                    fill_color = ACCENT_GOLD
                else:
                    fill_color = FUTURE_BOX

                outline = ACCENT_GOLD if idx == self.selected_week_idx else (TEXT_PRIMARY if has_note else "")
                width = 2 if idx == self.selected_week_idx else (1 if has_note else 0)

                rect_id = self.canvas.create_rectangle(
                    x0, y0, x1, y1, fill=fill_color, outline=outline, width=width
                )
                self.canvas.tag_bind(rect_id, "<Button-1>", lambda e, i=idx: self.on_week_click(i))
                self.canvas.tag_bind(rect_id, "<Double-Button-1>", lambda e, i=idx: self.on_week_double_click(i))

        self.canvas.config(scrollregion=(0, 0, total_canvas_w, total_canvas_h))

        if not self.initial_scroll_done:
            self.initial_scroll_done = True
            self.root.after(50, self.scroll_to_current_week)

    def on_week_click(self, week_idx: int):
        self.selected_week_idx = week_idx
        self.load_week_into_panels(week_idx)
        self.draw_life_grid()

    def on_week_double_click(self, week_idx: int):
        self.selected_week_idx = week_idx
        self.load_week_into_panels(week_idx)
        self.notebook.select(self.tab_week)

    def load_week_into_panels(self, week_idx: int):
        w_start, w_end = self.get_week_date_range(week_idx)
        age_yr = week_idx // 52
        wk_of_yr = (week_idx % 52) + 1
        curr = self.get_current_week_index()
        tag = " (CURRENT)" if week_idx == curr else ""

        self.ov_week_title.config(text=f"Age {age_yr} — Week {wk_of_yr}/52{tag}")
        self.ov_week_dates.config(text=f"{w_start.strftime('%b %d, %Y')}  →  {w_end.strftime('%b %d, %Y')}")

        w_data = self.data["weeks"].get(str(week_idx), {})
        cat = w_data.get("category")
        self.cat_var.set(cat if cat in self.data["categories"] else "(None / Default)")

        self.ov_note_text.delete("1.0", "end")
        self.ov_note_text.insert("1.0", w_data.get("note", ""))

        self.refresh_week_tab(week_idx)

    def save_overview_week_details(self):
        idx_str = str(self.selected_week_idx)
        if idx_str not in self.data["weeks"]:
            self.data["weeks"][idx_str] = {}

        selected_cat = self.cat_var.get()
        self.data["weeks"][idx_str]["category"] = (
            selected_cat if selected_cat in self.data["categories"] else None
        )
        self.data["weeks"][idx_str]["note"] = self.ov_note_text.get("1.0", "end").strip()
        self.save_data()
        self.draw_life_grid()

    def build_week_tab(self):
        top_bar = tk.Frame(self.tab_week, bg=BG_PANEL, height=52)
        top_bar.pack(fill="x", pady=(0, 10))
        top_bar.pack_propagate(False)

        tk.Button(
            top_bar,
            text="◀ Prev Week",
            font=("Segoe UI", 9, "bold"),
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            command=lambda: self.change_week(-1),
        ).pack(side="left", padx=14, pady=10)

        tk.Button(
            top_bar,
            text="Today (Current Week)",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_GOLD,
            fg="#121318",
            relief="flat",
            cursor="hand2",
            command=lambda: self.on_week_click(self.get_current_week_index()),
        ).pack(side="left", padx=4, pady=10)

        tk.Button(
            top_bar,
            text="Next Week ▶",
            font=("Segoe UI", 9, "bold"),
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            command=lambda: self.change_week(1),
        ).pack(side="left", padx=10, pady=10)

        self.wk_tab_header = tk.Label(
            top_bar, text="", font=("Segoe UI", 12, "bold"), bg=BG_PANEL, fg=TEXT_PRIMARY
        )
        self.wk_tab_header.pack(side="right", padx=20)

        self.days_container = tk.Frame(self.tab_week, bg=BG_MAIN)
        self.days_container.pack(fill="both", expand=True)

    def change_week(self, delta: int):
        max_w = (self.data["target_age"] * 52) - 1
        new_idx = max(0, min(max_w, self.selected_week_idx + delta))
        self.on_week_click(new_idx)

    def refresh_week_tab(self, week_idx: int):
        for w in self.days_container.winfo_children():
            w.destroy()

        w_start, w_end = self.get_week_date_range(week_idx)
        num_days = (w_end - w_start).days + 1
        age_yr = week_idx // 52
        wk_of_yr = (week_idx % 52) + 1

        self.wk_tab_header.config(
            text=f"Age {age_yr}, Week {wk_of_yr}/52  ({w_start.strftime('%Y-%m-%d')} to {w_end.strftime('%Y-%m-%d')})"
        )

        for col in range(10):
            self.days_container.columnconfigure(
                col, weight=1 if col < num_days else 0, uniform="day_col" if col < num_days else ""
            )
        self.days_container.rowconfigure(0, weight=1)

        idx_str = str(week_idx)
        w_data = self.data["weeks"].get(idx_str, {})
        days_data = w_data.get("days", {})
        today = date.today()

        for d_offset in range(num_days):
            day_date = w_start + timedelta(days=d_offset)
            d_key = str(d_offset)
            d_info = days_data.get(d_key, {"done": False, "color": BG_CARD, "note": ""})

            is_today = day_date == today
            card_bg = d_info.get("color") or BG_CARD
            border_col = ACCENT_GOLD if is_today else BORDER_COLOR

            card = tk.Frame(
                self.days_container,
                bg=card_bg,
                highlightbackground=border_col,
                highlightthickness=2 if is_today else 1,
            )
            card.grid(row=0, column=d_offset, sticky="nsew", padx=4, pady=4)

            day_name = day_date.strftime("%A")
            tk.Label(
                card,
                text=day_name,
                font=("Segoe UI", 10, "bold"),
                bg=card_bg,
                fg=ACCENT_GOLD if is_today else TEXT_PRIMARY,
            ).pack(pady=(12, 2))

            tk.Label(
                card,
                text=day_date.strftime("%b %d, %Y"),
                font=("Segoe UI", 9),
                bg=card_bg,
                fg=TEXT_MUTED,
            ).pack(pady=(0, 10))

            done_var = tk.BooleanVar(value=d_info.get("done", False))
            chk = tk.Checkbutton(
                card,
                text="Completed",
                variable=done_var,
                font=("Segoe UI", 9, "bold"),
                bg=card_bg,
                fg=ACCENT_GREEN if done_var.get() else TEXT_PRIMARY,
                selectcolor=BG_MAIN,
                activebackground=card_bg,
                activeforeground=TEXT_PRIMARY,
            )
            chk.pack(pady=(0, 8))

            def make_color_picker(offset_key=d_key, current_c=card_bg):
                def _pick():
                    c = colorchooser.askcolor(title="Day Card Color", initialcolor=current_c, parent=self.root)
                    if c and c[1]:
                        self._save_day_state(week_idx, offset_key, done_var.get(), c[1], note_box.get("1.0", "end").strip())
                        self.refresh_week_tab(week_idx)
                return _pick

            btn_row = tk.Frame(card, bg=card_bg)
            btn_row.pack(fill="x", padx=8, pady=(0, 8))

            tk.Button(
                btn_row,
                text="🎨 Color",
                font=("Segoe UI", 8),
                bg=BG_MAIN,
                fg=TEXT_PRIMARY,
                relief="flat",
                cursor="hand2",
                command=make_color_picker(),
            ).pack(side="left", expand=True, fill="x", padx=(0, 2))

            tk.Button(
                btn_row,
                text="Reset",
                font=("Segoe UI", 8),
                bg=BG_MAIN,
                fg=TEXT_MUTED,
                relief="flat",
                cursor="hand2",
                command=lambda k=d_key: (
                    self._save_day_state(week_idx, k, done_var.get(), BG_CARD, note_box.get("1.0", "end").strip()),
                    self.refresh_week_tab(week_idx),
                ),
            ).pack(side="right", expand=True, fill="x", padx=(2, 0))

            note_box = tk.Text(
                card,
                font=("Segoe UI", 9),
                bg=BG_MAIN,
                fg=TEXT_PRIMARY,
                insertbackground=TEXT_PRIMARY,
                relief="flat",
                wrap="word",
                padx=8,
                pady=8,
            )
            note_box.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            note_box.insert("1.0", d_info.get("note", ""))

            def make_saver(offset_key=d_key, v=done_var, c_bg=card_bg, nb=note_box):
                def _save():
                    self._save_day_state(week_idx, offset_key, v.get(), c_bg, nb.get("1.0", "end").strip())
                    self.refresh_week_tab(week_idx)
                return _save

            chk.config(command=make_saver())

            tk.Button(
                card,
                text="Save Day",
                font=("Segoe UI", 9, "bold"),
                bg=ACCENT_GREEN,
                fg="#FFFFFF",
                relief="flat",
                cursor="hand2",
                command=make_saver(),
            ).pack(fill="x", padx=8, pady=(0, 12), ipady=4)

    def _save_day_state(self, week_idx: int, day_key: str, done: bool, color: str, note: str):
        idx_str = str(week_idx)
        if idx_str not in self.data["weeks"]:
            self.data["weeks"][idx_str] = {}
        if "days" not in self.data["weeks"][idx_str]:
            self.data["weeks"][idx_str]["days"] = {}

        self.data["weeks"][idx_str]["days"][day_key] = {
            "done": done,
            "color": color,
            "note": note,
        }
        self.save_data()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = LifeApp(root)
        root.mainloop()
    except Exception:
        err_msg = traceback.format_exc()
        try:
            r = tk.Tk()
            r.withdraw()
            messagebox.showerror("Life App Error", f"An error occurred:\n\n{err_msg}")
        except Exception:
            pass
