import flet as ft
# Support older Flet versions
ft.icons = ft.Icons
ft.alignment.center = ft.alignment.Alignment.CENTER
ft.border = ft.Border
ft.padding = ft.Padding
ft.margin = ft.Margin

# Support page.dialog assignment for Flet 0.85 compatibility
def _get_page_dialog(self):
    return getattr(self, "_dialog_val", None)

def _set_page_dialog(self, value):
    self._dialog_val = value
    if value is not None:
        try:
            self.show_dialog(value)
        except Exception:
            pass

ft.Page.dialog = property(_get_page_dialog, _set_page_dialog)
import calendar
from datetime import datetime, date
import json
import csv
import io
import os
import sys

# Import database operations
import database

# Initialize the database
database.init_db()

class WorkoutApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "AetherFit - Home Workout Tracker"
        
        # OLED True Black Theme Configuration
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#000000"
        self.page.padding = 16
        
        # Custom Fonts and Color Palette
        self.primary_color = "#00F5D4"   # Neon Teal (Active / Done)
        self.secondary_color = "#9B5DE5" # Neon Purple (Planned)
        self.bg_card = "#0D0D0D"         # Very dark grey/black card
        self.border_color = "#1E1E1E"    # Subtle border
        self.text_muted = "#8E8E93"      # Muted grey text
        
        # Calendar State
        self.current_date = date.today()
        self.selected_date = date.today()
        self.view_year = self.selected_date.year
        self.view_month = self.selected_date.month
        
        # Cache for dates with workouts
        self.workout_dates = {}
        self.load_workout_dates()
        
        # UI Component references
        self.calendar_grid = ft.Column()
        self.calendar_header = ft.Row()
        self.day_details_card = ft.Column()
        self.exercises_list_view = ft.ListView(expand=True, spacing=10)
        self.stretches_list_view = ft.ListView(expand=True, spacing=10)
        self.search_field = ft.TextField()
        self.stretches_search_field = ft.TextField()
        
        # File pickers
        self.file_picker_export = ft.FilePicker()
        self.file_picker_import = ft.FilePicker()


    def load_workout_dates(self):
        # Reload dates that have workout logs for calendar dots
        self.workout_dates = database.get_workout_dates()

    def build_ui(self):
        # Main Navigation Tabs
        self.tabs = ft.Tabs(
            length=4,
            selected_index=0,
            animation_duration=250,
            on_change=self.on_tab_change,
            content=ft.TabBar(
                tabs=[
                    ft.Tab(label="Calendar", icon=ft.icons.CALENDAR_MONTH),
                    ft.Tab(label="Workout Lib", icon=ft.icons.FITNESS_CENTER),
                    ft.Tab(label="Stretch Lib", icon=ft.icons.ACCESSIBILITY_NEW),
                    ft.Tab(label="Settings", icon=ft.icons.SETTINGS),
                ]
            ),
            height=60
        )
        
        # Tab Content Area
        self.tab_content = ft.Container(expand=True, content=self.get_calendar_view())
        
        # Responsive Main Layout
        self.page.add(
            ft.Column(
                [
                    # Brand Header
                    ft.Row(
                        [
                            ft.Icon(icon=ft.icons.BOLT, color=self.primary_color, size=32),
                            ft.Text(
                                "AETHERFIT",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color="#FFFFFF",
                            ),
                            ft.Container(
                                content=ft.Text(
                                    "HOME EDITION",
                                    size=10,
                                    weight=ft.FontWeight.BOLD,
                                    color=self.primary_color,
                                ),
                                bgcolor="#112222",
                                padding=ft.padding.all(4),
                                border_radius=4,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=1, color=self.border_color),
                    self.tabs,
                    self.tab_content
                ],
                expand=True
            )
        )
        self.page.update()

    def on_tab_change(self, e):
        # Switch tab view
        idx = self.tabs.selected_index
        if idx == 0:
            self.load_workout_dates()
            self.tab_content.content = self.get_calendar_view()
        elif idx == 1:
            self.tab_content.content = self.get_library_view()
        elif idx == 2:
            self.tab_content.content = self.get_stretches_library_view()
        elif idx == 3:
            self.tab_content.content = self.get_settings_view()
        self.page.update()

    # ==========================================
    # TAB 1: CALENDAR & WORKOUT PLANNER
    # ==========================================
    def get_calendar_view(self):
        # Build components
        self.calendar_header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[]
        )
        self.update_calendar_header()
        
        self.calendar_grid = ft.Column(spacing=4)
        self.build_calendar_grid()
        
        self.day_details_card = ft.Column(expand=True, scroll=ft.ScrollMode.ADAPTIVE)
        self.update_day_details()

        # Layout adapting to desktop vs mobile
        # On PC we show side-by-side, on Mobile we stack
        is_desktop = self.page.width > 700 if self.page.width else False
        
        calendar_card = ft.Container(
            content=ft.Column(
                [
                    self.calendar_header,
                    ft.Container(height=10),
                    self.calendar_grid
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=self.bg_card,
            padding=12,
            border_radius=16,
            border=ft.border.all(1, self.border_color),
        )

        details_panel = ft.Container(
            content=self.day_details_card,
            bgcolor=self.bg_card,
            padding=16,
            border_radius=16,
            border=ft.border.all(1, self.border_color),
            expand=True
        )

        if is_desktop:
            # Side by side
            return ft.Row(
                [
                    ft.Container(content=calendar_card, width=360),
                    details_panel
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.START
            )
        else:
            # Vertical stack
            return ft.Column(
                [
                    calendar_card,
                    details_panel
                ],
                expand=True
            )

    def update_calendar_header(self):
        month_name = calendar.month_name[self.view_month]
        self.calendar_header.controls = [
            ft.IconButton(
                icon=ft.icons.CHEVRON_LEFT,
                icon_color=self.primary_color,
                on_click=self.prev_month
            ),
            ft.Text(
                f"{month_name} {self.view_year}".upper(),
                size=16,
                weight=ft.FontWeight.BOLD,
                color="#FFFFFF"
            ),
            ft.IconButton(
                icon=ft.icons.CHEVRON_RIGHT,
                icon_color=self.primary_color,
                on_click=self.next_month
            )
        ]

    def prev_month(self, e):
        if self.view_month == 1:
            self.view_month = 12
            self.view_year -= 1
        else:
            self.view_month -= 1
        self.update_calendar_header()
        self.build_calendar_grid()
        self.page.update()

    def next_month(self, e):
        if self.view_month == 12:
            self.view_month = 1
            self.view_year += 1
        else:
            self.view_month += 1
        self.update_calendar_header()
        self.build_calendar_grid()
        self.page.update()

    def build_calendar_grid(self):
        self.calendar_grid.controls.clear()
        
        # Day of week headers
        week_days = ["M", "T", "W", "T", "F", "S", "S"]
        days_header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            controls=[
                ft.Container(
                    content=ft.Text(day, size=12, weight=ft.FontWeight.BOLD, color=self.text_muted),
                    alignment=ft.alignment.center,
                    width=38,
                    height=30
                ) for day in week_days
            ]
        )
        self.calendar_grid.controls.append(days_header)

        # Get month matrix
        cal_obj = calendar.Calendar(firstweekday=0)
        weeks = cal_obj.monthdayscalendar(self.view_year, self.view_month)

        for week in weeks:
            row_controls = []
            for day in week:
                if day == 0:
                    # Empty space for days of adjacent months
                    row_controls.append(ft.Container(width=38, height=38))
                else:
                    cell_date = date(self.view_year, self.view_month, day)
                    is_selected = cell_date == self.selected_date
                    is_today = cell_date == date.today()
                    
                    # Check what logs exist on this date
                    date_str = cell_date.strftime("%Y-%m-%d")
                    has_planned = False
                    has_done = False
                    has_cardio = False
                    has_calories = False
                    has_body = False
                    has_stretch = False
                    if date_str in self.workout_dates:
                        has_planned = self.workout_dates[date_str].get("has_planned", False)
                        has_done = self.workout_dates[date_str].get("has_done", False)
                        has_cardio = self.workout_dates[date_str].get("has_cardio", False)
                        has_calories = self.workout_dates[date_str].get("has_calories", False)
                        has_body = self.workout_dates[date_str].get("has_body", False)
                        has_stretch = self.workout_dates[date_str].get("has_stretch", False)

                    # Indicator dots
                    dots = []
                    if has_done:
                        dots.append(ft.Container(width=4, height=4, border_radius=2, bgcolor=self.primary_color)) # Teal
                    if has_planned:
                        dots.append(ft.Container(width=4, height=4, border_radius=2, bgcolor=self.secondary_color)) # Purple
                    if has_cardio:
                        dots.append(ft.Container(width=4, height=4, border_radius=2, bgcolor="#3A86FF")) # Blue
                    if has_calories:
                        dots.append(ft.Container(width=4, height=4, border_radius=2, bgcolor="#FFBE0B")) # Yellow
                    if has_body:
                        dots.append(ft.Container(width=4, height=4, border_radius=2, bgcolor="#FF006E")) # Pink
                    if has_stretch:
                        dots.append(ft.Container(width=4, height=4, border_radius=2, bgcolor="#FB5607")) # Orange
                    
                    # Highlight selected or today
                    bg = None
                    border = None
                    text_color = "#FFFFFF"
                    
                    if is_selected:
                        bg = self.primary_color
                        text_color = "#000000"
                    elif is_today:
                        border = ft.border.all(1.5, self.primary_color)
                    else:
                        border = ft.border.all(1, self.border_color)

                    day_button = ft.GestureDetector(
                        on_tap=lambda e, d=cell_date: self.on_date_selected(d),
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(str(day), size=12, weight=ft.FontWeight.BOLD if (is_selected or is_today) else ft.FontWeight.NORMAL, color=text_color),
                                    ft.Row(dots, spacing=2, alignment=ft.MainAxisAlignment.CENTER) if dots else ft.Container(height=5)
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=2
                            ),
                            alignment=ft.alignment.center,
                            width=38,
                            height=38,
                            bgcolor=bg,
                            border_radius=8,
                            border=border,
                        )
                    )
                    row_controls.append(day_button)
            
            self.calendar_grid.controls.append(ft.Row(alignment=ft.MainAxisAlignment.SPACE_AROUND, controls=row_controls))

    def on_date_selected(self, selected_date):
        self.selected_date = selected_date
        self.view_year = selected_date.year
        self.view_month = selected_date.month
        self.update_calendar_header()
        self.build_calendar_grid()
        self.update_day_details()
        self.page.update()

    def update_day_details(self):
        self.day_details_card.controls.clear()
        
        formatted_date = self.selected_date.strftime("%A, %B %d, %Y")
        date_str = self.selected_date.strftime("%Y-%m-%d")
        
        # Header Row
        self.day_details_card.controls.append(
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("DAILY LOGS", size=10, color=self.primary_color, weight=ft.FontWeight.BOLD),
                            ft.Text(formatted_date, size=16, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                        ],
                        expand=True
                    ),
                    ft.IconButton(
                        icon=ft.icons.ADD_CIRCLE,
                        icon_color=self.primary_color,
                        icon_size=32,
                        tooltip="Add strength exercise to this day",
                        on_click=self.show_add_to_day_dialog
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )
        
        # Fetch other logs
        body_log = database.get_body_log(date_str)
        calories_log = database.get_calories_log(date_str)
        cardio_logs = database.get_cardio_logs(date_str)
        
        # --- BODY STATS CARD & CALORIES CARD ---
        weight_text = f"{body_log['weight']} kg" if body_log else "Log Weight"
        weight_sub = body_log['notes'] if (body_log and body_log['notes']) else "Tap to record weight"
        weight_color = "#FFFFFF" if body_log else self.text_muted
        weight_weight = ft.FontWeight.BOLD if body_log else ft.FontWeight.NORMAL
        
        weight_card = ft.GestureDetector(
            on_tap=lambda e: self.open_body_log_modal(date_str),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("BODY WEIGHT", size=9, color="#FF006E", weight=ft.FontWeight.BOLD),
                        ft.Text(weight_text, size=18, color=weight_color, weight=weight_weight),
                        ft.Text(weight_sub, size=11, color=self.text_muted, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
                    ],
                    spacing=4
                ),
                bgcolor="#0B0B0B",
                border=ft.border.all(1, self.border_color),
                border_radius=12,
                padding=12,
                expand=True
            )
        )

        calories_text = f"{calories_log['calories']} kcal" if calories_log else "Log Calories"
        if calories_log:
            calories_sub = f"P: {calories_log['protein']}g | C: {calories_log['carbs']}g | F: {calories_log['fat']}g"
        else:
            calories_sub = "Tap to record macros"
        calories_color = "#FFFFFF" if calories_log else self.text_muted
        calories_weight = ft.FontWeight.BOLD if calories_log else ft.FontWeight.NORMAL

        calories_card = ft.GestureDetector(
            on_tap=lambda e: self.open_calories_log_modal(date_str),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("NUTRITION", size=9, color="#FFBE0B", weight=ft.FontWeight.BOLD),
                        ft.Text(calories_text, size=18, color=calories_color, weight=calories_weight),
                        ft.Text(calories_sub, size=11, color=self.text_muted, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
                    ],
                    spacing=4
                ),
                bgcolor="#0B0B0B",
                border=ft.border.all(1, self.border_color),
                border_radius=12,
                padding=12,
                expand=True
            )
        )

        self.day_details_card.controls.append(
            ft.Row([weight_card, calories_card], spacing=10)
        )
        self.day_details_card.controls.append(ft.Divider(height=10, color=self.border_color))

        # --- CARDIO LOGS SECTION ---
        cardio_controls = []
        for c in cardio_logs:
            sub = f"{c['duration_minutes']} mins"
            if c['distance_km'] > 0:
                sub += f" | {c['distance_km']} km"
            if c['calories_burned'] > 0:
                sub += f" | {c['calories_burned']} kcal"
            
            def delete_cardio_action(log_id):
                database.delete_cardio_log(log_id)
                self.load_workout_dates()
                self.update_day_details()
                self.build_calendar_grid()
                self.page.update()

            cardio_controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(c['exercise_name'], size=14, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                    ft.Text(sub, size=12, color=self.text_muted),
                                    ft.Text(f"Notes: {c['notes']}", size=11, italic=True, color=self.text_muted) if c['notes'] else ft.Container()
                                ],
                                expand=True,
                                spacing=2
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE,
                                icon_color="#FF453A",
                                icon_size=18,
                                on_click=lambda e, cid=c['id']: delete_cardio_action(cid)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    bgcolor="#121212",
                    border=ft.border.all(1, "#1E1E1E"),
                    border_radius=8,
                    padding=8,
                    margin=ft.margin.only(bottom=5)
                )
            )

        cardio_header = ft.Row(
            [
                ft.Text("CARDIO ACTIVITIES", size=11, color="#3A86FF", weight=ft.FontWeight.BOLD),
                ft.IconButton(
                    icon=ft.icons.ADD_CIRCLE_OUTLINE,
                    icon_color="#3A86FF",
                    icon_size=20,
                    tooltip="Log Cardio Activity",
                    on_click=lambda e: self.open_add_cardio_modal(date_str)
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        self.day_details_card.controls.append(cardio_header)
        if cardio_controls:
            self.day_details_card.controls.extend(cardio_controls)
        else:
            self.day_details_card.controls.append(
                ft.Container(
                    content=ft.Text("No cardio logged today.", size=12, color=self.text_muted, italic=True),
                    margin=ft.margin.only(bottom=10)
                )
            )

        self.day_details_card.controls.append(ft.Divider(height=10, color=self.border_color))

        # --- STRETCHING LOGS SECTION ---
        stretching_logs = database.get_stretching_logs(date_str)
        planned_stretches = [l for l in stretching_logs if l['is_planned'] == 1]
        completed_stretches = [l for l in stretching_logs if l['is_planned'] == 0]

        stretching_header = ft.Row(
            [
                ft.Text("STRETCHING ACTIVITIES", size=11, color="#FB5607", weight=ft.FontWeight.BOLD),
                ft.IconButton(
                    icon=ft.icons.ADD_CIRCLE_OUTLINE,
                    icon_color="#FB5607",
                    icon_size=20,
                    tooltip="Log Stretch Activity",
                    on_click=self.show_add_stretch_to_day_dialog
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.day_details_card.controls.append(stretching_header)

        if not stretching_logs:
            self.day_details_card.controls.append(
                ft.Container(
                    content=ft.Text("No stretching logged or planned.", size=12, color=self.text_muted, italic=True),
                    margin=ft.margin.only(bottom=10)
                )
            )
        else:
            if planned_stretches:
                self.day_details_card.controls.append(
                    ft.Container(
                        content=ft.Text("PLANNED", size=9, color=self.secondary_color, weight=ft.FontWeight.BOLD),
                        margin=ft.margin.only(top=5, bottom=5)
                    )
                )
                for log in planned_stretches:
                    self.day_details_card.controls.append(self.build_stretching_log_tile(log))

            if completed_stretches:
                self.day_details_card.controls.append(
                    ft.Container(
                        content=ft.Text("COMPLETED", size=9, color="#FB5607", weight=ft.FontWeight.BOLD),
                        margin=ft.margin.only(top=5, bottom=5)
                    )
                )
                for log in completed_stretches:
                    self.day_details_card.controls.append(self.build_stretching_log_tile(log))

        self.day_details_card.controls.append(ft.Divider(height=10, color=self.border_color))

        # --- WORKOUT LOGS SECTION ---
        logs = database.get_workout_logs(date_str)
        planned_logs = [l for l in logs if l['is_planned'] == 1]
        completed_logs = [l for l in logs if l['is_planned'] == 0]

        workout_header = ft.Container(
            content=ft.Text("STRENGTH WORKOUTS", size=11, color=self.primary_color, weight=ft.FontWeight.BOLD),
            margin=ft.margin.only(bottom=5)
        )
        self.day_details_card.controls.append(workout_header)

        if not logs:
            self.day_details_card.controls.append(
                ft.Container(
                    content=ft.Text("No strength workouts logged or planned.", size=12, color=self.text_muted, italic=True),
                    margin=ft.margin.only(bottom=10)
                )
            )
        else:
            if planned_logs:
                self.day_details_card.controls.append(
                    ft.Container(
                        content=ft.Text("PLANNED", size=9, color=self.secondary_color, weight=ft.FontWeight.BOLD),
                        margin=ft.margin.only(top=5, bottom=5)
                    )
                )
                for log in planned_logs:
                    self.day_details_card.controls.append(self.build_workout_log_tile(log))

            if completed_logs:
                self.day_details_card.controls.append(
                    ft.Container(
                        content=ft.Text("COMPLETED", size=9, color=self.primary_color, weight=ft.FontWeight.BOLD),
                        margin=ft.margin.only(top=5, bottom=5)
                    )
                )
                for log in completed_logs:
                    self.day_details_card.controls.append(self.build_workout_log_tile(log))

    def build_workout_log_tile(self, log):
        # Load sets data from json
        try:
            sets = json.loads(log['sets_json'])
        except:
            sets = []

        is_planned = log['is_planned'] == 1
        accent = self.secondary_color if is_planned else self.primary_color
        
        # Summary text of sets (e.g. "3 sets x 12 reps")
        summary_text = ""
        if sets:
            set_counts = len(sets)
            reps_list = [f"{s.get('reps', 0)}r" if s.get('reps', 0) > 0 else f"{s.get('duration', 0)}s" for s in sets]
            summary_text = f"{set_counts} Set{'s' if set_counts > 1 else ''}: " + ", ".join(reps_list)
        else:
            summary_text = "No sets defined"

        # Workout log card tile
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(log['exercise_name'], size=16, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                            ft.Container(
                                                content=ft.Text(
                                                    log['exercise_category'].upper(),
                                                    size=9,
                                                    color=accent,
                                                    weight=ft.FontWeight.BOLD,
                                                ),
                                                bgcolor=f"{accent}22",
                                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                                border_radius=4
                                            )
                                        ],
                                        spacing=8
                                    ),
                                    ft.Text(summary_text, size=13, color=self.text_muted)
                                ],
                                expand=True
                            ),
                            # Action button
                            ft.IconButton(
                                icon=ft.icons.PLAY_ARROW if is_planned else ft.icons.EDIT,
                                icon_color=accent,
                                tooltip="Start / Log Workout" if is_planned else "Edit Log",
                                on_click=lambda e, l=log: self.open_log_workout_modal(l)
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE,
                                icon_color="#FF453A",
                                tooltip="Delete",
                                on_click=lambda e, l=log: self.delete_workout_log(l)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    # Show notes if they exist
                    ft.Container(
                        content=ft.Text(f"Notes: {log['notes']}", size=12, italic=True, color=self.text_muted),
                        margin=ft.margin.only(top=5)
                    ) if log.get('notes') else ft.Container()
                ]
            ),
            bgcolor="#121212",
            border=ft.border.all(1, "#1E1E1E"),
            border_radius=12,
            padding=12,
            margin=ft.margin.only(bottom=8)
        )

    def delete_workout_log(self, log):
        def do_delete(e):
            database.delete_workout_log(log['id'])
            self.load_workout_dates()
            self.update_day_details()
            self.build_calendar_grid()
            self.page.dialog.open = False
            self.page.update()

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Confirm Deletion"),
            content=ft.Text(f"Are you sure you want to remove the log for '{log['exercise_name']}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                ft.TextButton("Delete", on_click=do_delete, style=ft.ButtonStyle(color="#FF453A")),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    def close_dialog(self):
        try:
            self.page.pop_dialog()
        except Exception:
            pass
        if getattr(self.page, "dialog", None):
            self.page.dialog.open = False
        self.page.update()

    # ==========================================
    # MODAL: BODY WEIGHT LOG
    # ==========================================
    def open_body_log_modal(self, date_str):
        body_log = database.get_body_log(date_str)
        
        weight_input = ft.TextField(
            label="Body Weight (kg)",
            value=str(body_log['weight']) if body_log else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="#121212",
            border_color=self.border_color
        )
        
        notes_input = ft.TextField(
            label="Notes",
            value=body_log['notes'] if (body_log and body_log['notes']) else "",
            multiline=True,
            max_lines=2,
            bgcolor="#121212",
            border_color=self.border_color
        )
        
        err_msg = ft.Text("", color="#FF453A", size=13)

        def save_body(e):
            err_msg.value = ""
            try:
                weight = float(weight_input.value)
            except ValueError:
                err_msg.value = "Please enter a valid weight number."
                self.page.update()
                return

            success, err = database.save_body_log(date_str, weight, notes_input.value.strip())
            if success:
                self.load_workout_dates()
                self.update_day_details()
                self.build_calendar_grid()
                self.close_dialog()
            else:
                err_msg.value = err
                self.page.update()

        def delete_body(e):
            database.delete_body_log(date_str)
            self.load_workout_dates()
            self.update_day_details()
            self.build_calendar_grid()
            self.close_dialog()

        actions = [
            ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
            ft.ElevatedButton("Save", bgcolor="#FF006E", color="#FFFFFF", on_click=save_body)
        ]
        
        if body_log:
            actions.insert(1, ft.TextButton("Delete", style=ft.ButtonStyle(color="#FF453A"), on_click=delete_body))

        dialog = ft.AlertDialog(
            title=ft.Text("Log Body Weight", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        weight_input,
                        notes_input,
                        err_msg
                    ],
                    spacing=12,
                    expand=False
                ),
                width=320,
                height=180
            ),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#0A0A0A"
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    # ==========================================
    # MODAL: CALORIES LOG
    # ==========================================
    def open_calories_log_modal(self, date_str):
        cal_log = database.get_calories_log(date_str)
        
        cal_input = ft.TextField(
            label="Total Calories (kcal)",
            value=str(cal_log['calories']) if cal_log else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="#121212",
            border_color=self.border_color
        )
        
        protein_input = ft.TextField(
            label="Protein (g)",
            value=str(cal_log['protein']) if cal_log else "0.0",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=100,
            bgcolor="#121212",
            border_color=self.border_color
        )

        carbs_input = ft.TextField(
            label="Carbs (g)",
            value=str(cal_log['carbs']) if cal_log else "0.0",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=100,
            bgcolor="#121212",
            border_color=self.border_color
        )

        fat_input = ft.TextField(
            label="Fat (g)",
            value=str(cal_log['fat']) if cal_log else "0.0",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=100,
            bgcolor="#121212",
            border_color=self.border_color
        )

        notes_input = ft.TextField(
            label="Notes",
            value=cal_log['notes'] if (cal_log and cal_log['notes']) else "",
            multiline=True,
            max_lines=2,
            bgcolor="#121212",
            border_color=self.border_color
        )
        
        err_msg = ft.Text("", color="#FF453A", size=13)

        def save_calories(e):
            err_msg.value = ""
            try:
                calories = int(cal_input.value)
                protein = float(protein_input.value or 0.0)
                carbs = float(carbs_input.value or 0.0)
                fat = float(fat_input.value or 0.0)
            except ValueError:
                err_msg.value = "Calories, Protein, Carbs, and Fat must be valid numbers."
                self.page.update()
                return

            success, err = database.save_calories_log(date_str, calories, protein, carbs, fat, notes_input.value.strip())
            if success:
                self.load_workout_dates()
                self.update_day_details()
                self.build_calendar_grid()
                self.close_dialog()
            else:
                err_msg.value = err
                self.page.update()

        def delete_calories(e):
            database.delete_calories_log(date_str)
            self.load_workout_dates()
            self.update_day_details()
            self.build_calendar_grid()
            self.close_dialog()

        actions = [
            ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
            ft.ElevatedButton("Save", bgcolor="#FFBE0B", color="#000000", on_click=save_calories)
        ]
        
        if cal_log:
            actions.insert(1, ft.TextButton("Delete", style=ft.ButtonStyle(color="#FF453A"), on_click=delete_calories))

        dialog = ft.AlertDialog(
            title=ft.Text("Log Daily Calories / Macros", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        cal_input,
                        ft.Row(
                            [protein_input, carbs_input, fat_input],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        notes_input,
                        err_msg
                    ],
                    spacing=12,
                    expand=False,
                    scroll=ft.ScrollMode.ADAPTIVE
                ),
                width=340,
                height=350
            ),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#0A0A0A"
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    # ==========================================
    # MODAL: ADD CARDIO LOG
    # ==========================================
    def open_add_cardio_modal(self, date_str):
        exercise_input = ft.TextField(
            label="Cardio Activity (e.g. Running, Jump Rope)",
            bgcolor="#121212",
            border_color=self.border_color
        )
        
        duration_input = ft.TextField(
            label="Duration (minutes)",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="#121212",
            border_color=self.border_color
        )

        distance_input = ft.TextField(
            label="Distance (km, optional)",
            value="0.0",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="#121212",
            border_color=self.border_color
        )

        calories_input = ft.TextField(
            label="Calories Burned (kcal, optional)",
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="#121212",
            border_color=self.border_color
        )

        notes_input = ft.TextField(
            label="Notes",
            multiline=True,
            max_lines=2,
            bgcolor="#121212",
            border_color=self.border_color
        )
        
        err_msg = ft.Text("", color="#FF453A", size=13)

        def save_cardio(e):
            err_msg.value = ""
            name = exercise_input.value.strip()
            if not name:
                err_msg.value = "Activity name is required."
                self.page.update()
                return

            try:
                duration = float(duration_input.value)
                distance = float(distance_input.value or 0.0)
                calories = int(calories_input.value or 0)
            except ValueError:
                err_msg.value = "Duration, Distance, and Calories must be valid numbers."
                self.page.update()
                return

            database.add_cardio_log(date_str, name, duration, distance, calories, notes_input.value.strip())
            self.load_workout_dates()
            self.update_day_details()
            self.build_calendar_grid()
            self.close_dialog()

        dialog = ft.AlertDialog(
            title=ft.Text("Log Cardio Activity", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        exercise_input,
                        ft.Row(
                            [
                                ft.Container(content=duration_input, expand=True),
                                ft.Container(content=distance_input, expand=True)
                            ],
                            spacing=10
                        ),
                        calories_input,
                        notes_input,
                        err_msg
                    ],
                    spacing=12,
                    expand=False,
                    scroll=ft.ScrollMode.ADAPTIVE
                ),
                width=340,
                height=380
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                ft.ElevatedButton("Add Log", bgcolor="#3A86FF", color="#FFFFFF", on_click=save_cardio)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#0A0A0A"
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    # ==========================================
    # MODAL: LOG WORKOUT (INPUT REPS & MARK DONE)
    # ==========================================
    def open_log_workout_modal(self, log):
        # Get latest exercise information to display instructions
        exercise = database.get_exercise_by_id(log['exercise_id'])
        
        try:
            sets = json.loads(log['sets_json'])
        except:
            sets = []

        is_planned = log['is_planned'] == 1
        
        # State variables for logging modal
        modal_sets = list(sets) # copy
        set_rows_container = ft.Column(spacing=10)
        
        notes_input = ft.TextField(
            label="Workout Session Notes", 
            value=log['notes'] or "", 
            multiline=True,
            max_lines=3,
            bgcolor="#161616",
            border_color=self.border_color,
            text_size=14
        )

        # Instructions card (collapsible)
        instructions_text = ft.Text(
            exercise['instructions'] or "No instructions provided.",
            size=13,
            color="#E0E0E0"
        )
        
        instructions_box = ft.Container(
            content=ft.Column(
                [
                    ft.Text("INSTRUCTIONS", size=10, weight=ft.FontWeight.BOLD, color=self.primary_color),
                    instructions_text
                ],
                spacing=5
            ),
            bgcolor="#111111",
            padding=10,
            border_radius=8,
            border=ft.border.all(1, self.border_color),
            margin=ft.margin.only(bottom=10)
        )

        def build_set_rows():
            set_rows_container.controls.clear()
            for i, s in enumerate(modal_sets):
                # Reps/Duration Input field
                is_duration = exercise['default_duration'] > 0
                val_input = ft.TextField(
                    value=str(s.get('duration', 0) if is_duration else s.get('reps', 0)),
                    width=75,
                    height=40,
                    text_align=ft.TextAlign.CENTER,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    bgcolor="#181818",
                    border_color=self.border_color,
                    content_padding=5,
                    text_size=14,
                    on_change=lambda e, idx=i: on_set_metric_change(idx, e.control.value)
                )

                # Weight Input field
                weight_input = ft.TextField(
                    value=str(s.get('weight', 0)),
                    width=65,
                    height=40,
                    text_align=ft.TextAlign.CENTER,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    bgcolor="#181818",
                    border_color=self.border_color,
                    content_padding=5,
                    text_size=14,
                    on_change=lambda e, idx=i: on_set_weight_change(idx, e.control.value)
                )

                # Checkmark for completion
                completed = s.get('completed', 0) == 1
                checkmark = ft.IconButton(
                    icon=ft.icons.CHECK_BOX if completed else ft.icons.CHECK_BOX_OUTLINE_BLANK,
                    icon_color=self.primary_color if completed else self.text_muted,
                    on_click=lambda e, idx=i: toggle_set_completed(idx)
                )

                set_rows_container.controls.append(
                    ft.Row(
                        [
                            ft.Text(f"SET {i+1}", size=12, weight=ft.FontWeight.BOLD, width=50),
                            ft.Row(
                                [
                                    val_input,
                                    ft.Text("s" if is_duration else "r", size=13, color=self.text_muted)
                                ],
                                spacing=2,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            ft.Row(
                                [
                                    weight_input,
                                    ft.Text("kg", size=13, color=self.text_muted)
                                ],
                                spacing=2,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            checkmark,
                            ft.IconButton(
                                icon=ft.icons.REMOVE_CIRCLE_OUTLINE,
                                icon_color="#FF453A",
                                on_click=lambda e, idx=i: delete_set(idx)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    )
                )
            self.page.update()

        def on_set_metric_change(idx, val):
            try:
                num = int(val)
            except:
                num = 0
            if exercise['default_duration'] > 0:
                modal_sets[idx]['duration'] = num
            else:
                modal_sets[idx]['reps'] = num

        def on_set_weight_change(idx, val):
            try:
                num = float(val)
            except:
                num = 0.0
            modal_sets[idx]['weight'] = num

        def toggle_set_completed(idx):
            current = modal_sets[idx].get('completed', 0)
            modal_sets[idx]['completed'] = 0 if current == 1 else 1
            build_set_rows()

        def delete_set(idx):
            if len(modal_sets) > 1:
                modal_sets.pop(idx)
                build_set_rows()

        def add_set(e):
            # Duplicate the last set configuration
            if modal_sets:
                new_set = dict(modal_sets[-1])
                new_set['completed'] = 0
            else:
                new_set = {
                    "reps": exercise['default_reps'],
                    "duration": exercise['default_duration'],
                    "weight": 0.0,
                    "completed": 0
                }
            modal_sets.append(new_set)
            build_set_rows()

        def save_log(is_completing=False):
            # Save data back to DB
            sets_str = json.dumps(modal_sets)
            notes_str = notes_input.value
            
            # If completing, set is_planned = 0, otherwise keep existing state
            new_is_planned = 0 if is_completing else log['is_planned']
            comp_time = datetime.now().isoformat() if is_completing else log['completed_at']
            
            database.update_workout_log(log['id'], sets_str, notes_str, new_is_planned, comp_time)
            
            # Reload and update calendar dots + day details
            self.load_workout_dates()
            self.update_day_details()
            self.build_calendar_grid()
            self.close_dialog()

        # Build initial rows
        build_set_rows()

        # Dialog Buttons
        actions_list = [
            ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
            ft.ElevatedButton("Save Changes", on_click=lambda e: save_log(is_completing=False)),
        ]
        
        # If it was planned, add a big "Complete Workout" button
        if is_planned:
            actions_list.append(
                ft.ElevatedButton(
                    "Mark Completed", 
                    bgcolor=self.primary_color, 
                    color="#000000", 
                    on_click=lambda e: save_log(is_completing=True)
                )
            )
        else:
            # If it was completed, option to revert to planned
            def revert_to_planned(e):
                # Reset all completed flags inside sets
                for s in modal_sets:
                    s['completed'] = 0
                database.update_workout_log(log['id'], json.dumps(modal_sets), notes_input.value, 1, None)
                self.load_workout_dates()
                self.update_day_details()
                self.build_calendar_grid()
                self.close_dialog()

            actions_list.insert(1, ft.TextButton("Move back to Planned", on_click=revert_to_planned, style=ft.ButtonStyle(color=self.secondary_color)))

        log_dialog = ft.AlertDialog(
            title=ft.Text(f"Log {exercise['name']}", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        instructions_box,
                        ft.Row(
                            [
                                ft.Text("SETS LOG", size=10, weight=ft.FontWeight.BOLD, color=self.text_muted),
                                ft.IconButton(
                                    icon=ft.icons.ADD_CIRCLE_OUTLINE, 
                                    icon_color=self.primary_color, 
                                    on_click=add_set,
                                    tooltip="Add Set"
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        ft.Container(content=set_rows_container, margin=ft.margin.only(bottom=10)),
                        notes_input
                    ],
                    expand=False,
                    scroll=ft.ScrollMode.ADAPTIVE,
                    spacing=10
                ),
                width=350,
                height=500
            ),
            actions=actions_list,
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#0A0A0A"
        )
        
        self.page.dialog = log_dialog
        log_dialog.open = True
        self.page.update()


    # ==========================================
    # DIALOG: ADD WORKOUT TO DATE
    # ==========================================
    def show_add_to_day_dialog(self, e):
        # Fetch exercises
        exercises = database.get_exercises()
        
        search_field = ft.TextField(
            label="Search Exercises",
            prefix_icon=ft.icons.SEARCH,
            bgcolor="#121212",
            border_color=self.border_color,
            on_change=lambda e: filter_exercises(e.control.value)
        )
        
        exercise_cards_container = ft.Column(spacing=8, scroll=ft.ScrollMode.ADAPTIVE, expand=True)

        def plan_workout(ex_id):
            """Add as planned (no prompt needed — user will fill actuals when completing)."""
            ex = database.get_exercise_by_id(ex_id)
            sets_list = [
                {"reps": ex['default_reps'], "duration": ex['default_duration'], "weight": 0.0, "completed": 0}
                for _ in range(ex['default_sets'])
            ]
            date_str = self.selected_date.strftime("%Y-%m-%d")
            database.add_workout_log(date=date_str, exercise_id=ex_id,
                                     sets_json=json.dumps(sets_list), notes="",
                                     is_planned=1, completed_at=None)
            self.load_workout_dates()
            self.update_day_details()
            self.build_calendar_grid()
            self.close_dialog()

        def open_log_now_modal(ex_id):
            """Open a per-session input dialog so the user can enter actual weight/reps."""
            ex = database.get_exercise_by_id(ex_id)
            is_duration = ex['default_duration'] > 0

            # Build mutable sets list pre-filled with defaults
            modal_sets = [
                {"reps": ex['default_reps'], "duration": ex['default_duration'],
                 "weight": 0.0, "completed": 1}
                for _ in range(ex['default_sets'])
            ]

            set_rows_container = ft.Column(spacing=8)
            notes_input = ft.TextField(
                label="Session Notes",
                multiline=True, max_lines=2,
                bgcolor="#161616", border_color=self.border_color, text_size=13
            )

            def build_set_rows():
                set_rows_container.controls.clear()
                for i, s in enumerate(modal_sets):
                    val_field = ft.TextField(
                        value=str(s.get('duration', 0) if is_duration else s.get('reps', 0)),
                        width=70, height=38,
                        text_align=ft.TextAlign.CENTER,
                        keyboard_type=ft.KeyboardType.NUMBER,
                        bgcolor="#1A1A1A", border_color=self.border_color,
                        content_padding=4, text_size=14,
                        on_change=lambda e, idx=i: _set_metric(idx, e.control.value)
                    )
                    wt_field = ft.TextField(
                        value=str(s.get('weight', 0.0)),
                        width=65, height=38,
                        text_align=ft.TextAlign.CENTER,
                        keyboard_type=ft.KeyboardType.NUMBER,
                        bgcolor="#1A1A1A", border_color=self.border_color,
                        content_padding=4, text_size=14,
                        on_change=lambda e, idx=i: _set_weight(idx, e.control.value)
                    )
                    set_rows_container.controls.append(
                        ft.Row(
                            [
                                ft.Text(f"SET {i+1}", size=11, weight=ft.FontWeight.BOLD,
                                        color=self.text_muted, width=45),
                                ft.Row([val_field,
                                        ft.Text("s" if is_duration else "r", size=12, color=self.text_muted)],
                                       spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.Row([wt_field,
                                        ft.Text("kg", size=12, color=self.text_muted)],
                                       spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.IconButton(
                                    icon=ft.icons.REMOVE_CIRCLE_OUTLINE,
                                    icon_color="#FF453A", icon_size=18,
                                    on_click=lambda e, idx=i: _del_set(idx)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8
                        )
                    )
                self.page.update()

            def _set_metric(idx, val):
                try: num = int(val)
                except: num = 0
                if is_duration: modal_sets[idx]['duration'] = num
                else:           modal_sets[idx]['reps'] = num

            def _set_weight(idx, val):
                try: modal_sets[idx]['weight'] = float(val)
                except: modal_sets[idx]['weight'] = 0.0

            def _del_set(idx):
                if len(modal_sets) > 1:
                    modal_sets.pop(idx)
                    build_set_rows()

            def _add_set(e):
                new = dict(modal_sets[-1]) if modal_sets else \
                      {"reps": ex['default_reps'], "duration": ex['default_duration'],
                       "weight": 0.0, "completed": 1}
                new['completed'] = 1
                modal_sets.append(new)
                build_set_rows()

            def _save(e):
                date_str = self.selected_date.strftime("%Y-%m-%d")
                database.add_workout_log(
                    date=date_str, exercise_id=ex_id,
                    sets_json=json.dumps(modal_sets),
                    notes=notes_input.value,
                    is_planned=0,
                    completed_at=datetime.now().isoformat()
                )
                self.load_workout_dates()
                self.update_day_details()
                self.build_calendar_grid()
                self.close_dialog()

            build_set_rows()

            session_dialog = ft.AlertDialog(
                title=ft.Text(f"Log: {ex['name']}", size=17, weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        [
                            # Column headers
                            ft.Row(
                                [
                                    ft.Text("", width=45),
                                    ft.Text("Reps/Time", size=10, color=self.text_muted, width=85),
                                    ft.Text("Weight", size=10, color=self.text_muted, width=80),
                                ],
                                spacing=8
                            ),
                            set_rows_container,
                            ft.TextButton(
                                content="+ Add Set",
                                on_click=_add_set,
                                style=ft.ButtonStyle(color=self.primary_color)
                            ),
                            notes_input
                        ],
                        spacing=10, scroll=ft.ScrollMode.ADAPTIVE
                    ),
                    width=350, height=420
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                    ft.ElevatedButton(
                        content="Save Workout",
                        bgcolor=self.primary_color, color="#000000",
                        on_click=_save
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                bgcolor="#0A0A0A"
            )
            self.page.dialog = session_dialog
            session_dialog.open = True
            self.page.update()

        def build_exercise_cards(filter_text=""):
            exercise_cards_container.controls.clear()
            filtered = [ex for ex in exercises if filter_text.lower() in ex['name'].lower()
                        or filter_text.lower() in ex['category'].lower()]
            
            if not filtered:
                exercise_cards_container.controls.append(
                    ft.Text("No exercises found. Add one in the Library tab!",
                            size=13, color=self.text_muted, italic=True)
                )
            
            for ex in filtered:
                exercise_cards_container.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(ex['name'], size=14, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                        ft.Text(ex['category'].upper(), size=10,
                                                color=self.primary_color, weight=ft.FontWeight.BOLD)
                                    ],
                                    expand=True
                                ),
                                ft.Row(
                                    [
                                        ft.IconButton(
                                            icon=ft.icons.BOOKMARK_ADD_OUTLINED,
                                            icon_color=self.secondary_color,
                                            tooltip="Plan for later",
                                            on_click=lambda e, eid=ex['id']: plan_workout(eid)
                                        ),
                                        ft.IconButton(
                                            icon=ft.icons.EDIT_NOTE,
                                            icon_color=self.primary_color,
                                            tooltip="Log Now (enter weight & reps)",
                                            on_click=lambda e, eid=ex['id']: open_log_now_modal(eid)
                                        )
                                    ],
                                    spacing=2
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        bgcolor="#121212",
                        border=ft.border.all(1, "#1E1E1E"),
                        border_radius=8,
                        padding=10
                    )
                )
            self.page.update()

        def filter_exercises(val):
            build_exercise_cards(val)

        # Initial builder
        build_exercise_cards()

        add_dialog = ft.AlertDialog(
            title=ft.Text(f"Add Exercise to {self.selected_date.strftime('%b %d')}",
                          size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        search_field,
                        ft.Row([
                            ft.Icon(icon=ft.icons.BOOKMARK_ADD_OUTLINED,
                                    color=self.secondary_color, size=14),
                            ft.Text("Plan  ", size=11, color=self.text_muted),
                            ft.Icon(icon=ft.icons.EDIT_NOTE,
                                    color=self.primary_color, size=14),
                            ft.Text("Log Now", size=11, color=self.text_muted),
                        ], spacing=4),
                        ft.Container(height=6),
                        exercise_cards_container
                    ],
                    expand=False
                ),
                width=350,
                height=420
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.close_dialog())
            ],
            bgcolor="#0A0A0A"
        )
        self.page.dialog = add_dialog
        add_dialog.open = True
        self.page.update()


    # ==========================================
    # TAB 2: LIBRARY (EXERCISES DEFINITION)
    # ==========================================
    def get_library_view(self):
        # Search and actions row
        self.search_field = ft.TextField(
            label="Search exercises...",
            expand=True,
            prefix_icon=ft.icons.SEARCH,
            bgcolor=self.bg_card,
            border_color=self.border_color,
            on_change=self.on_library_search
        )
        
        add_btn = ft.ElevatedButton(
            content="NEW EXERCISE",
            icon=ft.icons.ADD,
            bgcolor=self.primary_color,
            color="#000000",
            on_click=lambda e: self.show_exercise_editor_dialog(e)
        )

        controls_row = ft.Row(
            [
                self.search_field,
                add_btn
            ],
            spacing=10
        )

        self.update_library_list()

        return ft.Column(
            [
                controls_row,
                ft.Container(height=10),
                ft.Text("YOUR EXERCISES", size=11, color=self.primary_color, weight=ft.FontWeight.BOLD),
                self.exercises_list_view
            ],
            expand=True
        )

    def on_library_search(self, e):
        self.update_library_list(e.control.value)

    def update_library_list(self, filter_text=""):
        self.exercises_list_view.controls.clear()
        exercises = database.get_exercises()
        
        filtered = [ex for ex in exercises if filter_text.lower() in ex['name'].lower() or filter_text.lower() in ex['category'].lower()]
        
        if not filtered:
            self.exercises_list_view.controls.append(
                ft.Container(
                    content=ft.Text("No exercises found.", color=self.text_muted, size=14),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
            self.page.update()
            return

        for ex in filtered:
            has_duration = ex['default_duration'] > 0
            default_metric = f"{ex['default_duration']}s" if has_duration else f"{ex['default_reps']} reps"
            sets_desc = f"{ex['default_sets']} sets x {default_metric}"
            
            card = ft.Container(
                content=ft.ExpansionTile(
                    title=ft.Row(
                        [
                            ft.Text(ex['name'], size=16, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                            ft.Container(
                                content=ft.Text(
                                    ex['category'].upper(),
                                    size=9,
                                    color=self.primary_color,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                bgcolor=f"{self.primary_color}22",
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                border_radius=4
                            )
                        ],
                        spacing=8
                    ),
                    subtitle=ft.Text(sets_desc, size=13, color=self.text_muted),
                    collapsed_bgcolor="#121212",
                    text_color="#FFFFFF",
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("INSTRUCTIONS ON HOW TO PERFORM:", size=11, color=self.primary_color, weight=ft.FontWeight.BOLD),
                                    ft.Text(ex['instructions'] or "No instructions written.", size=13, color="#D0D0D0"),
                                    ft.Row(
                                        [
                                            ft.TextButton(
                                                "Edit Exercise",
                                                icon=ft.icons.EDIT,
                                                on_click=lambda e, item=ex: self.show_exercise_editor_dialog(e, item)
                                            ),
                                            ft.TextButton(
                                                "Delete",
                                                icon=ft.icons.DELETE_OUTLINE,
                                                style=ft.ButtonStyle(color="#FF453A"),
                                                on_click=lambda e, item=ex: self.delete_exercise(item)
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.END
                                    )
                                ],
                                spacing=8
                            ),
                            padding=12,
                            bgcolor="#161616"
                        )
                    ]
                ),
                border=ft.border.all(1, self.border_color),
                border_radius=12,
                bgcolor="#121212",
                margin=ft.margin.only(bottom=8)
            )
            self.exercises_list_view.controls.append(card)
        
        self.page.update()

    def delete_exercise(self, ex):
        def do_delete(e):
            database.delete_exercise(ex['id'])
            self.update_library_list()
            self.load_workout_dates()
            self.page.dialog.open = False
            self.page.update()

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Confirm Deletion"),
            content=ft.Text(f"Warning: Deleting exercise '{ex['name']}' will also delete all associated historical logs. Are you sure?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                ft.TextButton("Delete Everything", on_click=do_delete, style=ft.ButtonStyle(color="#FF453A")),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    # ==========================================
    # DIALOG: EXERCISE EDITOR (ADD / EDIT)
    # ==========================================
    def show_exercise_editor_dialog(self, e, exercise_item=None):
        is_edit = exercise_item is not None
        
        # Form fields
        name_input = ft.TextField(
            label="Exercise Name (e.g. Diamond Push-ups)",
            value=exercise_item['name'] if is_edit else "",
            bgcolor="#121212",
            border_color=self.border_color
        )
        
        category_dropdown = ft.Dropdown(
            label="Category",
            value=exercise_item['category'] if is_edit else "Chest",
            options=[
                ft.dropdown.Option("Chest"),
                ft.dropdown.Option("Back"),
                ft.dropdown.Option("Legs"),
                ft.dropdown.Option("Core"),
                ft.dropdown.Option("Arms"),
                ft.dropdown.Option("Shoulders"),
                ft.dropdown.Option("Cardio"),
                ft.dropdown.Option("Custom")
            ],
            bgcolor="#121212",
            border_color=self.border_color
        )

        sets_input = ft.TextField(
            label="Default Sets",
            value=str(exercise_item['default_sets']) if is_edit else "3",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=100,
            bgcolor="#121212",
            border_color=self.border_color
        )

        reps_input = ft.TextField(
            label="Default Reps",
            value=str(exercise_item['default_reps']) if is_edit else "10",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=100,
            bgcolor="#121212",
            border_color=self.border_color
        )

        duration_input = ft.TextField(
            label="Duration (sec)",
            value=str(exercise_item['default_duration']) if is_edit else "0",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=100,
            bgcolor="#121212",
            border_color=self.border_color,
            tooltip="Set to 0 if reps-based. Use for hold exercises like Planks."
        )

        instructions_input = ft.TextField(
            label="Instructions / Explanation",
            value=exercise_item['instructions'] if is_edit else "",
            multiline=True,
            min_lines=3,
            max_lines=6,
            bgcolor="#121212",
            border_color=self.border_color,
            hint_text="Write detail instructions about hand placement, posture, tips on how you do it, progressions etc."
        )

        bodyweight_switch = ft.Switch(
            label="Bodyweight Exercise (No Weights)",
            value=exercise_item['is_bodyweight'] == 1 if is_edit else True,
            active_color=self.primary_color
        )

        err_msg = ft.Text("", color="#FF453A", size=13)

        def save_exercise(e):
            err_msg.value = ""
            name = name_input.value.strip()
            category = category_dropdown.value
            instructions = instructions_input.value.strip()
            
            try:
                sets = int(sets_input.value)
                reps = int(reps_input.value)
                duration = int(duration_input.value)
            except ValueError:
                err_msg.value = "Sets, Reps, and Duration must be valid numbers."
                self.page.update()
                return

            if not name:
                err_msg.value = "Exercise name is required."
                self.page.update()
                return

            is_bodyweight = 1 if bodyweight_switch.value else 0

            if is_edit:
                success, err = database.update_exercise(
                    exercise_item['id'], name, category, instructions, sets, reps, duration, is_bodyweight
                )
            else:
                success, err = database.add_exercise(
                    name, category, instructions, sets, reps, duration, is_bodyweight
                )

            if success:
                # Reload UI
                self.update_library_list(self.search_field.value)
                self.close_dialog()
            else:
                err_msg.value = err
                self.page.update()

        editor_dialog = ft.AlertDialog(
            title=ft.Text("Edit Exercise" if is_edit else "Create New Exercise", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        name_input,
                        category_dropdown,
                        ft.Row(
                            [sets_input, reps_input, duration_input],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        bodyweight_switch,
                        instructions_input,
                        err_msg
                    ],
                    spacing=12,
                    expand=False,
                    scroll=ft.ScrollMode.ADAPTIVE
                ),
                width=350,
                height=450
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                ft.ElevatedButton("Save", bgcolor=self.primary_color, color="#000000", on_click=save_exercise)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#0A0A0A"
        )

        self.page.dialog = editor_dialog
        editor_dialog.open = True
        self.page.update()


    # ==========================================
    # TAB 3: DATA MANAGEMENT & SETTINGS
    # ==========================================
    def get_settings_view(self):
        self.text_backup_area = ft.TextField(
            label="JSON Data Backup",
            multiline=True,
            min_lines=6,
            max_lines=10,
            text_size=12,
            bgcolor="#0A0A0A",
            border_color=self.border_color,
            read_only=False,
            hint_text="You can copy/paste raw database backups here to transfer workouts between mobile and PC easily!"
        )

        status_text = ft.Text("Version: 1.0 (OLED Optimized) | SQLite Engined", size=12, color=self.text_muted)

        # Card: Export options
        export_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text("EXPORT DATA", size=14, weight=ft.FontWeight.BOLD, color=self.primary_color),
                    ft.Text("Backup all your routines, historical logs, and exercises.", size=12, color=self.text_muted),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Generate Backup Text",
                                icon=ft.icons.CODE,
                                on_click=self.generate_backup_text
                            ),
                            ft.ElevatedButton(
                                "Save to JSON File",
                                icon=ft.icons.SAVE,
                                on_click=self.export_json_file
                            ),
                            ft.ElevatedButton(
                                "Export Logs to CSV",
                                icon=ft.icons.GRID_ON,
                                on_click=self.export_csv_file
                            )
                        ],
                        wrap=True,
                        spacing=10
                    )
                ],
                spacing=10
            ),
            bgcolor=self.bg_card,
            padding=16,
            border_radius=12,
            border=ft.border.all(1, self.border_color)
        )

        # Card: Import options
        import_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text("IMPORT DATA", size=14, weight=ft.FontWeight.BOLD, color=self.secondary_color),
                    ft.Text("Restore workouts from a JSON text backup or JSON file. Note: This will overwrite current data.", size=12, color=self.text_muted),
                    self.text_backup_area,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Import Backup Text",
                                icon=ft.icons.UPLOAD,
                                bgcolor=self.secondary_color,
                                color="#FFFFFF",
                                on_click=self.import_backup_text
                            ),
                            ft.ElevatedButton(
                                "Import JSON File",
                                icon=ft.icons.FILE_OPEN,
                                on_click=self.import_json_file
                            )
                        ],
                        wrap=True,
                        spacing=10
                    )
                ],
                spacing=10
            ),
            bgcolor=self.bg_card,
            padding=16,
            border_radius=12,
            border=ft.border.all(1, self.border_color)
        )

        # Card: Developer / Scalability info
        scalability_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text("FUTURE INTEGRATION ENGINE", size=14, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                    ft.Text(
                        "The backend is fully engineered on SQLite with pre-constructed schema tables for Calories Logs "
                        "and Cardio Logs. This means adding calorie calculations, macro counters, running stats, and "
                        "weight tracking later can be seamlessly connected without breaking your existing workout data.",
                        size=13,
                        color=self.text_muted
                    )
                ],
                spacing=8
            ),
            bgcolor="#111",
            padding=16,
            border_radius=12,
            border=ft.border.all(1, self.border_color)
        )

        return ft.Column(
            [
                export_card,
                ft.Container(height=10),
                import_card,
                ft.Container(height=10),
                scalability_card,
                ft.Container(height=15),
                status_text
            ],
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True
        )

    # Backup & Export Logic
    def generate_backup_text(self, e):
        data = database.export_data()
        self.text_backup_area.value = json.dumps(data, indent=2)
        self.page.update()
        
        # Copy to clipboard automatically
        self.page.set_clipboard(self.text_backup_area.value)
        
        # Show snackbar notification
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Data Backup JSON copied to clipboard!"),
            bgcolor=self.primary_color,
            font_size=13
        )
        self.page.snack_bar.open = True
        self.page.update()

    async def export_json_file(self, e):
        data = database.export_data()
        data_str = json.dumps(data, indent=4)
        data_bytes = data_str.encode("utf-8")
        
        try:
            path = await self.file_picker_export.save_file(
                file_name="aetherfit_backup.json",
                file_type=ft.FilePickerFileType.ANY,
                src_bytes=data_bytes
            )
            if path:
                if isinstance(path, str) and not self.page.web:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(data_str)
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Backup saved successfully!"),
                    bgcolor=self.primary_color
                )
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as ex:
            self.show_error_dialog(f"Failed to export JSON file: {str(ex)}")

    async def export_csv_file(self, e):
        logs = database.get_workout_logs()
        if not logs:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("No logs found to export!"), bgcolor="#FF453A")
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Date", "Exercise Name", "Category", 
            "Set Number", "Reps", "Duration (sec)", 
            "Weight (kg)", "Completed", "Completed At", "Notes"
        ])
        for log in logs:
            try:
                sets = json.loads(log['sets_json'])
            except:
                sets = []
            for idx, s in enumerate(sets):
                writer.writerow([
                    log['date'],
                    log['exercise_name'],
                    log['exercise_category'],
                    idx + 1,
                    s.get('reps', 0),
                    s.get('duration', 0),
                    s.get('weight', 0.0),
                    "Yes" if s.get('completed', 0) == 1 else "No",
                    log.get('completed_at') or "",
                    log.get('notes') or ""
                ])
        csv_str = output.getvalue()
        csv_bytes = csv_str.encode("utf-8")
        
        try:
            path = await self.file_picker_export.save_file(
                file_name="workout_history.csv",
                file_type=ft.FilePickerFileType.ANY,
                src_bytes=csv_bytes
            )
            if path:
                if isinstance(path, str) and not self.page.web:
                    with open(path, "w", newline="", encoding="utf-8") as f:
                        f.write(csv_str)
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Workout history exported successfully!"),
                    bgcolor=self.primary_color
                )
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as ex:
            self.show_error_dialog(f"Failed to export CSV: {str(ex)}")

    async def import_json_file(self, e):
        try:
            files = await self.file_picker_import.pick_files(
                allow_multiple=False,
                allowed_extensions=["json"],
                with_data=True
            )
            if files and files[0]:
                file_path = files[0].path
                if file_path and not self.page.web:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    if files[0].bytes:
                        data = json.loads(files[0].bytes.decode("utf-8"))
                    else:
                        raise ValueError("No file content read.")
                
                success, msg = database.import_data(data)
                if success:
                    self.load_workout_dates()
                    self.page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=self.primary_color)
                else:
                    self.show_error_dialog(msg)
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as ex:
            self.show_error_dialog(f"Failed to import JSON file: {str(ex)}")

    def import_backup_text(self, e):
        text_data = self.text_backup_area.value.strip()
        if not text_data:
            self.show_error_dialog("Please paste the JSON backup text in the box above.")
            return

        try:
            data = json.loads(text_data)
            success, msg = database.import_data(data)
            
            if success:
                self.load_workout_dates()
                self.page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=self.primary_color)
            else:
                self.show_error_dialog(msg)
                
            self.page.snack_bar.open = True
            self.page.update()
        except json.JSONDecodeError:
            self.show_error_dialog("Invalid JSON format. Please ensure you copied the entire backup correctly.")

    def show_error_dialog(self, message):
        error_dialog = ft.AlertDialog(
            title=ft.Text("Error", color="#FF453A"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.close_dialog())
            ]
        )
        self.page.dialog = error_dialog
        error_dialog.open = True
        self.page.update()

    # ==========================================
    # TAB 3: STRETCH LIBRARY
    # ==========================================
    def get_stretches_library_view(self):
        self.stretches_search_field = ft.TextField(
            label="Search stretches...",
            expand=True,
            prefix_icon=ft.icons.SEARCH,
            bgcolor=self.bg_card,
            border_color=self.border_color,
            on_change=self.on_stretches_library_search
        )
        
        add_btn = ft.ElevatedButton(
            content="NEW STRETCH",
            icon=ft.icons.ADD,
            bgcolor="#FB5607",
            color="#000000",
            on_click=lambda e: self.show_stretch_editor_dialog(e)
        )

        controls_row = ft.Row(
            [
                self.stretches_search_field,
                add_btn
            ],
            spacing=10
        )

        self.update_stretches_library_list()

        return ft.Column(
            [
                controls_row,
                ft.Container(height=10),
                ft.Text("YOUR STRETCHES", size=11, color="#FB5607", weight=ft.FontWeight.BOLD),
                self.stretches_list_view
            ],
            expand=True
        )

    def on_stretches_library_search(self, e):
        self.update_stretches_library_list(e.control.value)

    def update_stretches_library_list(self, filter_text=""):
        self.stretches_list_view.controls.clear()
        stretches = database.get_stretches()
        
        filtered = [st for st in stretches if filter_text.lower() in st['name'].lower() or filter_text.lower() in st['category'].lower()]
        
        if not filtered:
            self.stretches_list_view.controls.append(
                ft.Container(
                    content=ft.Text("No stretches found.", color=self.text_muted, size=14),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
            self.page.update()
            return

        for st in filtered:
            sets_desc = f"{st['default_sets']} sets x {st['default_duration']}s"
            
            card = ft.Container(
                content=ft.ExpansionTile(
                    title=ft.Row(
                        [
                            ft.Text(st['name'], size=16, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                            ft.Container(
                                content=ft.Text(
                                    st['category'].upper(),
                                    size=9,
                                    color="#FB5607",
                                    weight=ft.FontWeight.BOLD,
                                ),
                                bgcolor=f"#FB560722",
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                border_radius=4
                            )
                        ],
                        spacing=8
                    ),
                    subtitle=ft.Text(sets_desc, size=13, color=self.text_muted),
                    collapsed_bgcolor="#121212",
                    text_color="#FFFFFF",
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("INSTRUCTIONS ON HOW TO PERFORM:", size=11, color="#FB5607", weight=ft.FontWeight.BOLD),
                                    ft.Text(st['instructions'] or "No instructions written.", size=13, color="#D0D0D0"),
                                    ft.Row(
                                        [
                                            ft.TextButton(
                                                "Edit Stretch",
                                                icon=ft.icons.EDIT,
                                                on_click=lambda e, item=st: self.show_stretch_editor_dialog(e, item)
                                            ),
                                            ft.TextButton(
                                                "Delete",
                                                icon=ft.icons.DELETE_OUTLINE,
                                                style=ft.ButtonStyle(color="#FF453A"),
                                                on_click=lambda e, item=st: self.delete_stretch(item)
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.END
                                    )
                                ],
                                spacing=8
                            ),
                            padding=12,
                            bgcolor="#161616"
                        )
                    ]
                ),
                border=ft.border.all(1, self.border_color),
                border_radius=12,
                bgcolor="#121212",
                margin=ft.margin.only(bottom=8)
            )
            self.stretches_list_view.controls.append(card)
        
        self.page.update()

    def delete_stretch(self, st):
        def do_delete(e):
            database.delete_stretch(st['id'])
            self.update_stretches_library_list()
            self.load_workout_dates()
            self.close_dialog()

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Confirm Deletion"),
            content=ft.Text(f"Warning: Deleting stretch '{st['name']}' will also delete all associated historical logs. Are you sure?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                ft.TextButton("Delete Everything", on_click=do_delete, style=ft.ButtonStyle(color="#FF453A")),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    def show_stretch_editor_dialog(self, e, stretch_item=None):
        is_edit = stretch_item is not None
        
        name_input = ft.TextField(
            label="Stretch Name (e.g. Couch Stretch)",
            value=stretch_item['name'] if is_edit else "",
            bgcolor="#121212",
            border_color=self.border_color
        )
        
        category_dropdown = ft.Dropdown(
            label="Target Area / Category",
            value=stretch_item['category'] if is_edit else "Legs",
            options=[
                ft.dropdown.Option("Legs"),
                ft.dropdown.Option("Back"),
                ft.dropdown.Option("Chest"),
                ft.dropdown.Option("Shoulders"),
                ft.dropdown.Option("Core"),
                ft.dropdown.Option("Full Body"),
                ft.dropdown.Option("Custom")
            ],
            bgcolor="#121212",
            border_color=self.border_color
        )

        sets_input = ft.TextField(
            label="Default Sets",
            value=str(stretch_item['default_sets']) if is_edit else "3",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=120,
            bgcolor="#121212",
            border_color=self.border_color
        )

        duration_input = ft.TextField(
            label="Duration (sec)",
            value=str(stretch_item['default_duration']) if is_edit else "30",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=120,
            bgcolor="#121212",
            border_color=self.border_color
        )

        instructions_input = ft.TextField(
            label="Instructions / Explanation",
            value=stretch_item['instructions'] if is_edit else "",
            multiline=True,
            min_lines=3,
            max_lines=6,
            bgcolor="#121212",
            border_color=self.border_color,
            hint_text="Write detail instructions about setup, hold, breathing, modifications etc."
        )

        err_msg = ft.Text("", color="#FF453A", size=13)

        def save_stretch(e):
            err_msg.value = ""
            name = name_input.value.strip()
            category = category_dropdown.value
            instructions = instructions_input.value.strip()
            
            try:
                sets = int(sets_input.value)
                duration = int(duration_input.value)
            except ValueError:
                err_msg.value = "Sets and Duration must be valid numbers."
                self.page.update()
                return

            if not name:
                err_msg.value = "Stretch name is required."
                self.page.update()
                return

            if is_edit:
                success, err = database.update_stretch(
                    stretch_item['id'], name, category, instructions, sets, duration
                )
            else:
                _, err = database.add_stretch(name, category, instructions, sets, duration)
                success = err is None

            if success:
                self.update_stretches_library_list()
                self.close_dialog()
            else:
                err_msg.value = err or "An error occurred."
                self.page.update()

        editor_dialog = ft.AlertDialog(
            title=ft.Text("Edit Stretch" if is_edit else "Add Stretch", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        name_input,
                        category_dropdown,
                        ft.Row(
                            [sets_input, duration_input],
                            spacing=10
                        ),
                        instructions_input,
                        err_msg
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.ADAPTIVE
                ),
                width=350,
                height=450
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                ft.ElevatedButton(
                    content="Save Stretch",
                    bgcolor="#FB5607",
                    color="#000000",
                    on_click=save_stretch
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#0A0A0A"
        )
        self.page.dialog = editor_dialog
        editor_dialog.open = True
        self.page.update()

    # ==========================================
    # MODAL: LOG STRETCH
    # ==========================================
    def open_log_stretch_modal(self, log):
        stretch = database.get_stretch_by_id(log['stretch_id'])
        
        try:
            sets = json.loads(log['sets_json'])
        except:
            sets = []

        is_planned = log['is_planned'] == 1
        modal_sets = list(sets) # copy
        set_rows_container = ft.Column(spacing=10)
        
        notes_input = ft.TextField(
            label="Stretch Session Notes", 
            value=log['notes'] or "", 
            multiline=True,
            max_lines=3,
            bgcolor="#161616",
            border_color=self.border_color,
            text_size=14
        )

        instructions_box = ft.Container(
            content=ft.Column(
                [
                    ft.Text("INSTRUCTIONS", size=10, weight=ft.FontWeight.BOLD, color="#FB5607"),
                    ft.Text(stretch['instructions'] or "No instructions provided.", size=13, color="#E0E0E0")
                ],
                spacing=5
            ),
            bgcolor="#111111",
            padding=10,
            border_radius=8,
            border=ft.border.all(1, self.border_color),
            margin=ft.margin.only(bottom=10)
        )

        def build_set_rows():
            set_rows_container.controls.clear()
            for i, s in enumerate(modal_sets):
                val_input = ft.TextField(
                    value=str(s.get('duration', 30)),
                    width=100,
                    height=40,
                    text_align=ft.TextAlign.CENTER,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    bgcolor="#181818",
                    border_color=self.border_color,
                    content_padding=5,
                    text_size=14,
                    on_change=lambda e, idx=i: on_set_duration_change(idx, e.control.value)
                )

                completed = s.get('completed', 0) == 1
                checkmark = ft.IconButton(
                    icon=ft.icons.CHECK_BOX if completed else ft.icons.CHECK_BOX_OUTLINE_BLANK,
                    icon_color="#FB5607" if completed else self.text_muted,
                    on_click=lambda e, idx=i: toggle_set_completed(idx)
                )

                set_rows_container.controls.append(
                    ft.Row(
                        [
                            ft.Text(f"SET {i+1}", size=12, weight=ft.FontWeight.BOLD, width=50),
                            ft.Row(
                                [
                                    val_input,
                                    ft.Text("seconds", size=13, color=self.text_muted)
                                ],
                                spacing=4,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            checkmark,
                            ft.IconButton(
                                icon=ft.icons.REMOVE_CIRCLE_OUTLINE,
                                icon_color="#FF453A",
                                on_click=lambda e, idx=i: delete_set(idx)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    )
                )
            self.page.update()

        def on_set_duration_change(idx, val):
            try:
                num = int(val)
            except:
                num = 0
            modal_sets[idx]['duration'] = num

        def toggle_set_completed(idx):
            current = modal_sets[idx].get('completed', 0)
            modal_sets[idx]['completed'] = 0 if current == 1 else 1
            build_set_rows()

        def delete_set(idx):
            if len(modal_sets) > 1:
                modal_sets.pop(idx)
                build_set_rows()

        def add_set(e):
            if modal_sets:
                new_set = dict(modal_sets[-1])
                new_set['completed'] = 0
            else:
                new_set = {
                    "duration": stretch['default_duration'],
                    "completed": 0
                }
            modal_sets.append(new_set)
            build_set_rows()

        def save_log(is_completing=False):
            sets_str = json.dumps(modal_sets)
            notes_str = notes_input.value
            new_is_planned = 0 if is_completing else log['is_planned']
            comp_time = datetime.now().isoformat() if is_completing else log['completed_at']
            database.update_stretching_log(log['id'], sets_str, notes_str, new_is_planned, comp_time)
            self.load_workout_dates()
            self.update_day_details()
            self.build_calendar_grid()
            self.close_dialog()

        build_set_rows()

        actions_list = [
            ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
            ft.ElevatedButton("Save Changes", on_click=lambda e: save_log(is_completing=False)),
        ]
        
        if is_planned:
            actions_list.append(
                ft.ElevatedButton(
                    "Mark Completed", 
                    bgcolor="#FB5607", 
                    color="#000000", 
                    on_click=lambda e: save_log(is_completing=True)
                )
            )
        else:
            def revert_to_planned(e):
                for s in modal_sets:
                    s['completed'] = 0
                database.update_stretching_log(log['id'], json.dumps(modal_sets), notes_input.value, 1, None)
                self.load_workout_dates()
                self.update_day_details()
                self.build_calendar_grid()
                self.close_dialog()
            actions_list.insert(1, ft.TextButton("Move back to Planned", on_click=revert_to_planned, style=ft.ButtonStyle(color=self.secondary_color)))

        log_dialog = ft.AlertDialog(
            title=ft.Text(f"Log {stretch['name']}", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        instructions_box,
                        ft.Row(
                            [
                                ft.Text("SETS LOG", size=10, weight=ft.FontWeight.BOLD, color=self.text_muted),
                                ft.IconButton(
                                    icon=ft.icons.ADD,
                                    icon_color="#FB5607",
                                    icon_size=16,
                                    on_click=add_set
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        set_rows_container,
                        ft.Container(height=10),
                        notes_input
                    ],
                    spacing=5,
                    scroll=ft.ScrollMode.ADAPTIVE
                ),
                width=350,
                height=450
            ),
            actions=actions_list,
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#0A0A0A"
        )
        self.page.dialog = log_dialog
        log_dialog.open = True
        self.page.update()

    # ==========================================
    # DIALOG: ADD STRETCH TO DATE
    # ==========================================
    def show_add_stretch_to_day_dialog(self, e):
        stretches = database.get_stretches()
        
        search_field = ft.TextField(
            label="Search Stretches",
            prefix_icon=ft.icons.SEARCH,
            bgcolor="#121212",
            border_color=self.border_color,
            on_change=lambda e: filter_stretches(e.control.value)
        )
        
        stretch_cards_container = ft.Column(spacing=8, scroll=ft.ScrollMode.ADAPTIVE, expand=True)

        def plan_stretch(stretch_id):
            st = database.get_stretch_by_id(stretch_id)
            sets_list = [
                {"duration": st['default_duration'], "completed": 0}
                for _ in range(st['default_sets'])
            ]
            date_str = self.selected_date.strftime("%Y-%m-%d")
            database.add_stretching_log(date=date_str, stretch_id=stretch_id,
                                        sets_json=json.dumps(sets_list), notes="",
                                        is_planned=1, completed_at=None)
            self.load_workout_dates()
            self.update_day_details()
            self.build_calendar_grid()
            self.close_dialog()

        def open_log_now_modal(stretch_id):
            st = database.get_stretch_by_id(stretch_id)
            modal_sets = [
                {"duration": st['default_duration'], "completed": 1}
                for _ in range(st['default_sets'])
            ]

            set_rows_container = ft.Column(spacing=8)
            notes_input = ft.TextField(
                label="Session Notes",
                multiline=True, max_lines=2,
                bgcolor="#161616", border_color=self.border_color, text_size=13
            )

            def build_set_rows():
                set_rows_container.controls.clear()
                for i, s in enumerate(modal_sets):
                    val_field = ft.TextField(
                        value=str(s.get('duration', 30)),
                        width=80, height=38,
                        text_align=ft.TextAlign.CENTER,
                        keyboard_type=ft.KeyboardType.NUMBER,
                        bgcolor="#1A1A1A", border_color=self.border_color,
                        content_padding=4, text_size=14,
                        on_change=lambda e, idx=i: _set_duration(idx, e.control.value)
                    )
                    set_rows_container.controls.append(
                        ft.Row(
                            [
                                ft.Text(f"SET {i+1}", size=11, weight=ft.FontWeight.BOLD,
                                        color=self.text_muted, width=45),
                                ft.Row([val_field,
                                        ft.Text("seconds", size=12, color=self.text_muted)],
                                       spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.IconButton(
                                    icon=ft.icons.REMOVE_CIRCLE_OUTLINE,
                                    icon_color="#FF453A", icon_size=18,
                                    on_click=lambda e, idx=i: _del_set(idx)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8
                        )
                    )
                self.page.update()

            def _set_duration(idx, val):
                try: num = int(val)
                except: num = 0
                modal_sets[idx]['duration'] = num

            def _del_set(idx):
                if len(modal_sets) > 1:
                    modal_sets.pop(idx)
                    build_set_rows()

            def _add_set(e):
                new = dict(modal_sets[-1]) if modal_sets else \
                      {"duration": st['default_duration'], "completed": 1}
                new['completed'] = 1
                modal_sets.append(new)
                build_set_rows()

            def _save(e):
                date_str = self.selected_date.strftime("%Y-%m-%d")
                database.add_stretching_log(
                    date=date_str, stretch_id=stretch_id,
                    sets_json=json.dumps(modal_sets),
                    notes=notes_input.value,
                    is_planned=0,
                    completed_at=datetime.now().isoformat()
                )
                self.load_workout_dates()
                self.update_day_details()
                self.build_calendar_grid()
                self.close_dialog()

            build_set_rows()

            session_dialog = ft.AlertDialog(
                title=ft.Text(f"Log: {st['name']}", size=17, weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text("", width=45),
                                    ft.Text("Duration", size=10, color=self.text_muted, width=120),
                                ],
                                spacing=8
                            ),
                            set_rows_container,
                            ft.TextButton(
                                content="+ Add Set",
                                on_click=_add_set,
                                style=ft.ButtonStyle(color="#FB5607")
                            ),
                            notes_input
                        ],
                        spacing=10, scroll=ft.ScrollMode.ADAPTIVE
                    ),
                    width=350, height=420
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                    ft.ElevatedButton(
                        content="Save Stretch",
                        bgcolor="#FB5607", color="#000000",
                        on_click=_save
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                bgcolor="#0A0A0A"
            )
            self.page.dialog = session_dialog
            session_dialog.open = True
            self.page.update()

        def build_stretch_cards(filter_text=""):
            stretch_cards_container.controls.clear()
            filtered = [st for st in stretches if filter_text.lower() in st['name'].lower()
                        or filter_text.lower() in st['category'].lower()]
            
            if not filtered:
                stretch_cards_container.controls.append(
                    ft.Text("No stretches found. Add one in the Stretch Library tab!",
                            size=13, color=self.text_muted, italic=True)
                )
            
            for st in filtered:
                stretch_cards_container.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(st['name'], size=14, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                        ft.Text(st['category'].upper(), size=10,
                                                color="#FB5607", weight=ft.FontWeight.BOLD)
                                    ],
                                    expand=True
                                ),
                                ft.Row(
                                    [
                                        ft.IconButton(
                                            icon=ft.icons.BOOKMARK_ADD_OUTLINED,
                                            icon_color=self.secondary_color,
                                            tooltip="Plan for later",
                                            on_click=lambda e, sid=st['id']: plan_stretch(sid)
                                        ),
                                        ft.IconButton(
                                            icon=ft.icons.EDIT_NOTE,
                                            icon_color="#FB5607",
                                            tooltip="Log Now (enter duration)",
                                            on_click=lambda e, sid=st['id']: open_log_now_modal(sid)
                                        )
                                    ],
                                    spacing=2
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        bgcolor="#121212",
                        border=ft.border.all(1, "#1E1E1E"),
                        border_radius=8,
                        padding=10
                    )
                )
            self.page.update()

        def filter_stretches(val):
            build_stretch_cards(val)

        build_stretch_cards()

        add_dialog = ft.AlertDialog(
            title=ft.Text(f"Add Stretch to {self.selected_date.strftime('%b %d')}",
                          size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        search_field,
                        ft.Row([
                            ft.Icon(icon=ft.icons.BOOKMARK_ADD_OUTLINED,
                                    color=self.secondary_color, size=14),
                            ft.Text("Plan  ", size=11, color=self.text_muted),
                            ft.Icon(icon=ft.icons.EDIT_NOTE,
                                    color="#FB5607", size=14),
                            ft.Text("Log Now", size=11, color=self.text_muted),
                        ], spacing=4),
                        ft.Container(height=6),
                        stretch_cards_container
                    ],
                    expand=False
                ),
                width=350,
                height=420
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.close_dialog())
            ],
            bgcolor="#0A0A0A"
        )
        self.page.dialog = add_dialog
        add_dialog.open = True
        self.page.update()

    def build_stretching_log_tile(self, log):
        try:
            sets = json.loads(log['sets_json'])
        except:
            sets = []

        is_planned = log['is_planned'] == 1
        accent = self.secondary_color if is_planned else "#FB5607"
        
        summary_text = ""
        if sets:
            set_counts = len(sets)
            duration_list = [f"{s.get('duration', 30)}s" for s in sets]
            summary_text = f"{set_counts} Set{'s' if set_counts > 1 else ''}: " + ", ".join(duration_list)
        else:
            summary_text = "No sets defined"

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(log['stretch_name'], size=16, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                            ft.Container(
                                                content=ft.Text(
                                                    log['stretch_category'].upper(),
                                                    size=9,
                                                    color=accent,
                                                    weight=ft.FontWeight.BOLD,
                                                ),
                                                bgcolor=f"{accent}22",
                                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                                border_radius=4
                                            )
                                        ],
                                        spacing=8
                                    ),
                                    ft.Text(summary_text, size=13, color=self.text_muted)
                                ],
                                expand=True
                            ),
                            ft.IconButton(
                                icon=ft.icons.PLAY_ARROW if is_planned else ft.icons.EDIT,
                                icon_color=accent,
                                tooltip="Start / Log Stretch" if is_planned else "Edit Log",
                                on_click=lambda e, l=log: self.open_log_stretch_modal(l)
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE,
                                icon_color="#FF453A",
                                tooltip="Delete",
                                on_click=lambda e, l=log: self.delete_stretching_log(l)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Container(
                        content=ft.Text(f"Notes: {log['notes']}", size=12, italic=True, color=self.text_muted),
                        margin=ft.margin.only(top=5)
                    ) if log.get('notes') else ft.Container()
                ]
            ),
            bgcolor="#121212",
            border=ft.border.all(1, "#1E1E1E"),
            border_radius=12,
            padding=12,
            margin=ft.margin.only(bottom=8)
        )

    def delete_stretching_log(self, log):
        def do_delete(e):
            database.delete_stretching_log(log['id'])
            self.load_workout_dates()
            self.update_day_details()
            self.build_calendar_grid()
            self.close_dialog()

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Delete Stretch Log"),
            content=ft.Text(f"Are you sure you want to delete the log for '{log['stretch_name']}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                ft.TextButton("Delete", on_click=do_delete, style=ft.ButtonStyle(color="#FF453A")),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    def show_error_dialog(self, message):
        error_dialog = ft.AlertDialog(
            title=ft.Text("Error", color="#FF453A"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.close_dialog())
            ]
        )
        self.page.dialog = error_dialog
        error_dialog.open = True
        self.page.update()


def main(page: ft.Page):
    app = WorkoutApp(page)
    app.build_ui()

if __name__ == "__main__":
    import sys
    if "--web" in sys.argv:
        ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)
    else:
        ft.app(target=main)
