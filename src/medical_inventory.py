"""
Medical Inventory System - Main Application (Kivy)
NASA HUNCH Project 2025-26

Manages medical inventory with barcode scanning,
facial recognition, and usage tracking.
"""

import os
import sys
import datetime
import threading
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import (
    StringProperty, ListProperty, BooleanProperty,
    NumericProperty, ObjectProperty
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp

import facial_recognition as fr
from database import DatabaseManager, PersonalDatabaseManager
from facial_recognition import FaceRecognitionError

# ============================================================================
# CONSTANTS
# ============================================================================

REFRESH_INTERVAL = 300  # seconds
ADMIN_CODE = "1234"

COLUMNS = [
    ("drug",       "Drug",       220),
    ("barcode",    "Barcode",    170),
    ("est_amount", "Amt~",       100),
    ("exp_date",   "Expiration", 140),
    ("type_",      "Type",       120),
    ("dose_size",  "Dose Size",  140),
    ("item_loc",   "Location",   100),
]

# ============================================================================
# KV LANGUAGE
# ============================================================================

KV = """
#:import dp kivy.metrics.dp

<ThemedLabel@Label>:
    font_size: dp(16)
    color: 1, 1, 1, 1

<ThemedButton@Button>:
    font_size: dp(16)
    size_hint_y: None
    height: dp(50)
    background_color: 0.24, 0.51, 0.78, 1
    background_normal: ''

<DangerButton@ThemedButton>:
    background_color: 0.7, 0.13, 0.13, 1

<SuccessButton@ThemedButton>:
    background_color: 0.13, 0.77, 0.37, 1

# --- Numpad Widget (reusable) ---
<NumpadWidget>:
    cols: 3
    spacing: dp(8)
    size_hint_y: None
    height: dp(280)

# --- Message Popup ---
<MessagePopup>:
    size_hint: 0.5, 0.4
    auto_dismiss: True
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        canvas.before:
            Color:
                rgba: 0.16, 0.16, 0.18, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]
        Label:
            text: root.message
            font_size: dp(16)
            text_size: self.width, None
            halign: 'center'
            valign: 'middle'
            size_hint_y: 0.7
        ThemedButton:
            text: 'OK'
            on_release: root.dismiss()
            size_hint_x: 0.5
            pos_hint: {'center_x': 0.5}

# --- Confirm Popup ---
<ConfirmPopup>:
    size_hint: 0.5, 0.4
    auto_dismiss: False
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        canvas.before:
            Color:
                rgba: 0.16, 0.16, 0.18, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]
        Label:
            text: root.message
            font_size: dp(16)
            text_size: self.width, None
            halign: 'center'
            valign: 'middle'
            size_hint_y: 0.6
        BoxLayout:
            size_hint_y: 0.4
            spacing: dp(12)
            ThemedButton:
                text: 'Yes'
                on_release: root.on_yes()
            DangerButton:
                text: 'No'
                on_release: root.on_no()

# --- Input Popup (barcode / amount / admin / date) ---
<InputPopup>:
    size_hint: 0.55, 0.75
    auto_dismiss: False
    BoxLayout:
        orientation: 'vertical'
        padding: dp(15)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: 0.16, 0.16, 0.18, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]
        Label:
            text: root.prompt
            font_size: dp(18)
            size_hint_y: None
            height: dp(40)
        TextInput:
            id: input_field
            text: root.input_text
            font_size: dp(20)
            size_hint_y: None
            height: dp(50)
            multiline: False
            password: root.is_password
            on_text: root.input_text = self.text
            on_text_validate: root.on_ok()
        NumpadWidget:
            id: numpad
            on_key: root.on_numpad_key(args[1])
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(12)
            ThemedButton:
                text: 'OK'
                on_release: root.on_ok()
            Button:
                text: 'Cancel'
                font_size: dp(16)
                size_hint_y: None
                height: dp(50)
                background_color: 0.35, 0.35, 0.35, 1
                background_normal: ''
                on_release: root.on_cancel()

# --- Virtual Keyboard Popup ---
<VirtualKeyboardPopup>:
    size_hint: 0.85, 0.8
    auto_dismiss: False
    BoxLayout:
        orientation: 'vertical'
        padding: dp(15)
        spacing: dp(8)
        canvas.before:
            Color:
                rgba: 0.16, 0.16, 0.18, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]
        Label:
            text: root.prompt
            font_size: dp(18)
            size_hint_y: None
            height: dp(35)
        TextInput:
            id: kb_input
            text: root.input_text
            font_size: dp(18)
            size_hint_y: None
            height: dp(48)
            multiline: False
            on_text: root.input_text = self.text
        BoxLayout:
            id: keyboard_rows
            orientation: 'vertical'
            spacing: dp(4)
            size_hint_y: 0.65
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(12)
            SuccessButton:
                text: 'OK'
                on_release: root.on_ok()
            Button:
                text: 'Cancel'
                font_size: dp(16)
                size_hint_y: None
                height: dp(50)
                background_color: 0.35, 0.35, 0.35, 1
                background_normal: ''
                on_release: root.on_cancel()

# --- Choice Popup (Restock / Use Item) ---
<ChoicePopup>:
    size_hint: 0.5, 0.45
    auto_dismiss: False
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        canvas.before:
            Color:
                rgba: 0.16, 0.16, 0.18, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]
        Label:
            text: 'Select Action Type'
            font_size: dp(22)
            bold: True
            size_hint_y: None
            height: dp(40)
        Label:
            text: 'Choose whether to restock an item or log usage:'
            font_size: dp(15)
            text_size: self.width, None
            halign: 'center'
            size_hint_y: None
            height: dp(40)
        BoxLayout:
            spacing: dp(12)
            size_hint_y: None
            height: dp(55)
            SuccessButton:
                text: 'Restock'
                on_release: root.choose('restock')
            ThemedButton:
                text: 'Use Item'
                on_release: root.choose('use')
            Button:
                text: 'Cancel'
                font_size: dp(16)
                size_hint_y: None
                height: dp(50)
                background_color: 0.35, 0.35, 0.35, 1
                background_normal: ''
                on_release: root.choose(None)

# --- Data Row ---
<DataRow>:
    size_hint_y: None
    height: dp(44)
    spacing: dp(2)
    canvas.before:
        Color:
            rgba: (0.24, 0.44, 0.65, 0.6) if self.selected else (0.17, 0.17, 0.17, 1)
        Rectangle:
            pos: self.pos
            size: self.size

# --- Header Row ---
<HeaderRow>:
    size_hint_y: None
    height: dp(44)
    spacing: dp(2)
    canvas.before:
        Color:
            rgba: 0.25, 0.25, 0.28, 1
        Rectangle:
            pos: self.pos
            size: self.size

# --- Main Screen ---
<MainScreen>:
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 0.11, 0.11, 0.12, 1
            Rectangle:
                pos: self.pos
                size: self.size

        # Title bar
        Label:
            text: 'Medical Inventory System'
            font_size: dp(28)
            bold: True
            size_hint_y: None
            height: dp(60)

        BoxLayout:
            padding: dp(10)
            spacing: dp(10)

            # Sidebar
            BoxLayout:
                orientation: 'vertical'
                size_hint_x: 0.28
                spacing: dp(10)
                padding: dp(8)
                canvas.before:
                    Color:
                        rgba: 0.14, 0.14, 0.16, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8)]

                # Search
                Label:
                    text: 'Search'
                    font_size: dp(16)
                    size_hint_y: None
                    height: dp(30)
                    halign: 'left'
                    text_size: self.width, None
                BoxLayout:
                    size_hint_y: None
                    height: dp(42)
                    spacing: dp(6)
                    TextInput:
                        id: search_input
                        hint_text: 'Search all fields...'
                        font_size: dp(15)
                        multiline: False
                        size_hint_x: 0.8
                        on_text: root.apply_filters()
                    Button:
                        text: chr(0x2328)
                        font_size: dp(18)
                        size_hint_x: 0.2
                        background_normal: ''
                        background_color: 0.24, 0.51, 0.78, 1
                        on_release: root.show_search_keyboard()

                # Filter
                Label:
                    text: 'Filters'
                    font_size: dp(16)
                    size_hint_y: None
                    height: dp(30)
                    halign: 'left'
                    text_size: self.width, None
                Spinner:
                    id: filter_spinner
                    text: 'All'
                    values: ['All', 'Expiring Soon', 'Expired']
                    size_hint_y: None
                    height: dp(42)
                    font_size: dp(15)
                    on_text: root.apply_filters()
                BoxLayout:
                    size_hint_y: None
                    height: dp(36)
                    spacing: dp(6)
                    CheckBox:
                        id: low_stock_cb
                        size_hint_x: None
                        width: dp(36)
                        active: False
                        on_active: root.apply_filters()
                    Label:
                        text: 'Show low stock only'
                        font_size: dp(14)
                        halign: 'left'
                        text_size: self.width, None

                # Column visibility
                Label:
                    text: 'Show Columns'
                    font_size: dp(16)
                    size_hint_y: None
                    height: dp(30)
                    halign: 'left'
                    text_size: self.width, None
                ScrollView:
                    size_hint_y: 1
                    GridLayout:
                        id: col_checks
                        cols: 1
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(4)

                # Action buttons
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: dp(330)
                    spacing: dp(8)
                    padding: [0, dp(6)]

                    ThemedButton:
                        id: log_btn
                        text: 'Log Item Use'
                        on_release: root.log_item_use()
                    ThemedButton:
                        id: personal_btn
                        text: 'View Personal Database'
                        on_release: root.personal_run()
                    ThemedButton:
                        text: 'Delete Selected'
                        on_release: root.delete_selected()
                    ThemedButton:
                        text: 'View History'
                        on_release: root.show_history()
                    DangerButton:
                        text: 'Quit'
                        on_release: app.stop()

            # Content (data table)
            BoxLayout:
                orientation: 'vertical'
                canvas.before:
                    Color:
                        rgba: 0.14, 0.14, 0.16, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8)]

                HeaderRow:
                    id: header_row

                ScrollView:
                    id: table_scroll
                    GridLayout:
                        id: table_body
                        cols: 1
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(1)

# --- History Screen ---
<HistoryScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: 0.11, 0.11, 0.12, 1
            Rectangle:
                pos: self.pos
                size: self.size

        BoxLayout:
            size_hint_y: None
            height: dp(55)
            spacing: dp(10)
            ThemedButton:
                text: 'Pattern Recognition'
                on_release: root.show_pattern_rec()
                size_hint_x: 0.3
            Widget:
                size_hint_x: 0.4
            DangerButton:
                text: 'Close'
                on_release: root.go_back()
                size_hint_x: 0.3

        HeaderRow:
            id: hist_header

        ScrollView:
            GridLayout:
                id: hist_body
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(1)

# --- Personal DB Screen ---
<PersonalScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(8)
        spacing: dp(6)
        canvas.before:
            Color:
                rgba: 0.11, 0.11, 0.12, 1
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            id: title_label
            text: 'Personal Database'
            font_size: dp(24)
            bold: True
            size_hint_y: None
            height: dp(45)

        # Date navigation
        BoxLayout:
            size_hint_y: None
            height: dp(42)
            spacing: dp(10)
            ThemedButton:
                text: '<< Previous Day'
                on_release: root.previous_day()
                size_hint_x: 0.25
            Label:
                id: date_label
                text: ''
                font_size: dp(18)
                bold: True
                size_hint_x: 0.5
            ThemedButton:
                text: 'Next Day >>'
                on_release: root.next_day()
                size_hint_x: 0.25

        # Prescriptions
        Label:
            text: 'Scheduled Prescriptions'
            font_size: dp(16)
            bold: True
            size_hint_y: None
            height: dp(30)
            halign: 'left'
            text_size: self.width, None

        ScrollView:
            size_hint_y: 0.3
            GridLayout:
                id: presc_body
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(1)

        # Usage History
        Label:
            text: 'Usage History (Today)'
            font_size: dp(16)
            bold: True
            size_hint_y: None
            height: dp(30)
            halign: 'left'
            text_size: self.width, None

        ScrollView:
            size_hint_y: 0.3
            GridLayout:
                id: hist_body
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(1)

        # As-needed
        Label:
            text: 'As-Needed Medications'
            font_size: dp(16)
            bold: True
            size_hint_y: None
            height: dp(30)
            halign: 'left'
            text_size: self.width, None

        ScrollView:
            size_hint_y: 0.15
            GridLayout:
                id: as_needed_body
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(1)

        # Controls
        BoxLayout:
            size_hint_y: None
            height: dp(46)
            spacing: dp(8)
            ThemedButton:
                text: 'Use Item'
                on_release: root.use_item_from_personal()
            SuccessButton:
                text: 'Today'
                on_release: root.goto_today()
            DangerButton:
                text: 'Close'
                on_release: root.go_back()
"""

Builder.load_string(KV)


# ============================================================================
# REUSABLE WIDGETS (DRY)
# ============================================================================

class NumpadWidget(GridLayout):
    """Reusable numpad grid. Dispatches 'on_key' with the key character."""

    def __init__(self, **kwargs):
        self.register_event_type('on_key')
        super().__init__(**kwargs)
        self._build()

    def _build(self):
        self.clear_widgets()
        keys = [
                '7', '8', '9',
                '4', '5', '6',
                '1', '2', '3',
                'C', '0', '<'
            ]
        for k in keys:
            btn = Button(
                text=k, font_size=dp(22),
                background_normal='',
                background_color=(0.25, 0.25, 0.28, 1),
            )
            btn.bind(on_release=lambda inst, key=k: self.dispatch('on_key', key))
            self.add_widget(btn)

    def on_key(self, *args):
        pass


class MessagePopup(Popup):
    """Simple message popup with OK button."""
    message = StringProperty('')

    def __init__(self, title='Info', message='', **kwargs):
        super().__init__(title=title, **kwargs)
        self.message = message


class ConfirmPopup(Popup):
    """Yes/No confirmation popup."""
    message = StringProperty('')
    callback = ObjectProperty(None, allownone=True)

    def __init__(self, title='Confirm', message='', callback=None, **kwargs):
        super().__init__(title=title, **kwargs)
        self.message = message
        self.callback = callback

    def on_yes(self):
        if self.callback:
            self.callback(True)
        self.dismiss()

    def on_no(self):
        if self.callback:
            self.callback(False)
        self.dismiss()


class InputPopup(Popup):
    """Modal input with numpad. Calls callback(value) on OK, callback(None) on cancel."""
    prompt = StringProperty('')
    input_text = StringProperty('')
    is_password = BooleanProperty(False)
    callback = ObjectProperty(None, allownone=True)
    validate_number = BooleanProperty(False)

    def __init__(self, title='Input', prompt='Enter value:', callback=None,
                 initial_text='', is_password=False, validate_number=False, **kwargs):
        super().__init__(title=title, **kwargs)
        self.prompt = prompt
        self.input_text = initial_text
        self.callback = callback
        self.is_password = is_password
        self.validate_number = validate_number

    def on_numpad_key(self, key):
        if key == 'C':
            self.input_text = ''
        elif key == '<':
            self.input_text = self.input_text[:-1]
        else:
            self.input_text += key

    def on_ok(self):
        val = self.input_text.strip()
        if not val:
            return
        if self.validate_number:
            try:
                float(val)
            except ValueError:
                MessagePopup(title='Invalid', message='Please enter a valid number.').open()
                return
        if self.callback:
            self.callback(val)
        self.dismiss()

    def on_cancel(self):
        if self.callback:
            self.callback(None)
        self.dismiss()


class ChoicePopup(Popup):
    """Restock / Use Item / Cancel chooser."""
    callback = ObjectProperty(None, allownone=True)

    def __init__(self, callback=None, **kwargs):
        super().__init__(title='Log Item Use', **kwargs)
        self.callback = callback

    def choose(self, choice):
        if self.callback:
            self.callback(choice)
        self.dismiss()


class VirtualKeyboardPopup(Popup):
    """Full QWERTY virtual keyboard popup."""
    prompt = StringProperty('')
    input_text = StringProperty('')
    callback = ObjectProperty(None, allownone=True)

    ROWS = [
        list('1234567890-='),
        list('qwertyuiop[]'),
        list("asdfghjkl;'"),
        list('zxcvbnm,./'),
    ]

    def __init__(self, title='Keyboard', prompt='Enter text:',
                 callback=None, initial_text='', **kwargs):
        super().__init__(title=title, **kwargs)
        self.prompt = prompt
        self.input_text = initial_text
        self.callback = callback
        self._shift = False
        Clock.schedule_once(self._build_keyboard, 0)

    def _build_keyboard(self, dt):
        container = self.ids.keyboard_rows
        container.clear_widgets()
        for row in self.ROWS:
            row_box = BoxLayout(spacing=dp(3), size_hint_y=None, height=dp(48))
            for key in row:
                btn = Button(
                    text=key, font_size=dp(16),
                    background_normal='',
                    background_color=(0.25, 0.25, 0.28, 1),
                )
                btn.bind(on_release=lambda inst, k=key: self._key_press(k))
                row_box.add_widget(btn)
            container.add_widget(row_box)
        # Bottom row: Shift, Space, Backspace, Clear
        bottom = BoxLayout(spacing=dp(3), size_hint_y=None, height=dp(48))
        actions = [
            ('Shift', self._toggle_shift),
            ('Space', lambda: self._key_press(' ')),
            (chr(0x232B), self._backspace),
            ('Clear', self._clear),
        ]
        for text, action in actions:
            btn = Button(
                text=text, font_size=dp(14),
                background_normal='',
                background_color=(0.3, 0.3, 0.33, 1),
            )
            btn.bind(on_release=lambda inst, a=action: a())
            bottom.add_widget(btn)
        container.add_widget(bottom)

    def _key_press(self, key):
        ch = key.upper() if self._shift else key
        self.input_text += ch
        if self._shift:
            self._shift = False

    def _toggle_shift(self):
        self._shift = not self._shift

    def _backspace(self):
        self.input_text = self.input_text[:-1]

    def _clear(self):
        self.input_text = ''

    def on_ok(self):
        if self.callback:
            self.callback(self.input_text.strip())
        self.dismiss()

    def on_cancel(self):
        if self.callback:
            self.callback(None)
        self.dismiss()


# ============================================================================
# TABLE ROWS
# ============================================================================

class DataRow(BoxLayout):
    """A single selectable data row in the table."""
    selected = BooleanProperty(False)
    row_data = ListProperty([])

    def __init__(self, values, **kwargs):
        super().__init__(**kwargs)
        self.row_data = list(values)
        for val in values:
            lbl = Label(
                text=str(val), font_size=dp(14),
                halign='left', valign='middle',
            )
            lbl.bind(size=lbl.setter('text_size'))
            self.add_widget(lbl)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.selected = not self.selected
            return True
        return super().on_touch_down(touch)


class HeaderRow(BoxLayout):
    """Column header row."""
    pass


# ============================================================================
# SCREENS
# ============================================================================

class MainScreen(Screen):
    """Main inventory screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self._all_rows = []
        self.fr_ready = False
        self.camera_ready = False
        self.visible_columns = {col_id: True for col_id, _, _ in COLUMNS}
        Clock.schedule_once(self._init_ui, 0)

    def _init_ui(self, dt):
        self._build_header()
        self._build_column_checkboxes()
        self._start_preloading()
        self._start_camera_monitor()
        self.load_data()
        Clock.schedule_interval(lambda dt: self.load_data(), REFRESH_INTERVAL)

    # --- Column checkboxes ---
    def _build_column_checkboxes(self):
        container = self.ids.col_checks
        container.clear_widgets()
        for col_id, label, _ in COLUMNS:
            row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
            cb = CheckBox(active=True, size_hint_x=None, width=dp(32))
            cb.bind(active=lambda inst, val, cid=col_id: self._toggle_column(cid, val))
            row.add_widget(cb)
            row.add_widget(Label(text=label, font_size=dp(14), halign='left',
                                 text_size=(None, None)))
            container.add_widget(row)

    def _toggle_column(self, col_id, visible):
        self.visible_columns[col_id] = visible
        self._build_header()
        self.apply_filters()

    # --- Header ---
    def _build_header(self):
        header = self.ids.header_row
        header.clear_widgets()
        for col_id, label, _ in COLUMNS:
            if self.visible_columns.get(col_id, True):
                lbl = Label(text=label, font_size=dp(15), bold=True,
                            halign='left', valign='middle')
                lbl.bind(size=lbl.setter('text_size'))
                header.add_widget(lbl)

    # --- Data loading ---
    def load_data(self):
        try:
            self._all_rows = list(self.db.pull_data("drugs_in_inventory"))
        except Exception as e:
            print(f"Error loading data: {e}")
            self._all_rows = []
        self.apply_filters()

    def apply_filters(self, *args):
        body = self.ids.table_body
        body.clear_widgets()

        query = self.ids.search_input.text.strip().lower()
        mode = self.ids.filter_spinner.text
        low_only = self.ids.low_stock_cb.active
        now = datetime.date.today()

        visible_ids = [cid for cid, _, _ in COLUMNS if self.visible_columns.get(cid, True)]

        filtered = []
        for row in self._all_rows:
            try:
                drug, barcode, est_amount = row[0], row[1], row[2]
                exp_date_raw, type_, dose_size, item_loc = row[3], row[4], row[5], row[6]
            except (IndexError, ValueError):
                continue

            # Search
            if query:
                fields = [str(v).lower() for v in (drug, barcode, type_, dose_size, item_loc)]
                if not any(query in f for f in fields):
                    continue

            # Low stock
            if low_only:
                try:
                    if float(est_amount) > 20:
                        continue
                except (ValueError, TypeError):
                    continue

            # Expiration
            exp_date = self._parse_date(exp_date_raw)
            if mode == "Expired" and (not exp_date or exp_date >= now):
                continue
            if mode == "Expiring Soon":
                if not exp_date:
                    continue
                delta = (exp_date - now).days
                if delta < 0 or delta > 30:
                    continue

            full = (drug, barcode, est_amount, exp_date_raw, type_, dose_size, item_loc)
            display = tuple(
                full[i] for i, (cid, _, _) in enumerate(COLUMNS)
                if cid in visible_ids
            )
            filtered.append((full, display))

        filtered.sort(key=lambda x: str(x[0][0]).lower())

        for full, display in filtered:
            dr = DataRow(display)
            dr.row_data = list(full)
            body.add_widget(dr)

    @staticmethod
    def _parse_date(d):
        if not d:
            return None
        if isinstance(d, datetime.date):
            return d
        s = str(d).strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        return None

    # --- Facial recognition ---
    def _start_preloading(self):
        def worker():
            try:
                result = fr.preload_everything()
                if result == FaceRecognitionError.SUCCESS:
                    self.fr_ready = fr.preloading_complete
                    self.camera_ready = fr.camera_ready
                else:
                    self.fr_ready = False
                    self.camera_ready = False
                    Clock.schedule_once(lambda dt: MessagePopup(
                        title='FR Init Error', message=str(result)
                    ).open(), 0.5)
            except Exception as e:
                print(f"Preloading error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def _start_camera_monitor(self):
        def monitor():
            interval = 5
            while True:
                try:
                    if not self.camera_ready and self.fr_ready:
                        if fr.reinitialize_camera():
                            self.camera_ready = True
                            fr.camera_ready = True
                            interval = 5
                        else:
                            interval = min(interval * 1.5, 120)
                    else:
                        interval = 5
                    time.sleep(interval)
                except Exception:
                    time.sleep(10)
        threading.Thread(target=monitor, daemon=True).start()

    def scan_face(self, purpose, callback):
        """Run face recognition in background thread, then call callback(name) on main thread."""
        if not self.fr_ready:
            MessagePopup(title='Please Wait', message='System is still loading.').open()
            return
        if not self.camera_ready:
            if not fr.reinitialize_camera():
                MessagePopup(title='Camera Error', message='Camera not found.').open()
                return
            self.camera_ready = True
            fr.camera_ready = True

        def worker():
            try:
                result = fr.quick_detect() if self.fr_ready else fr.main()
                Clock.schedule_once(lambda dt: self._handle_fr_result(result, callback), 0)
            except Exception:
                Clock.schedule_once(lambda dt: callback(None), 0)
        threading.Thread(target=worker, daemon=True).start()

    def _handle_fr_result(self, result, callback):
        if isinstance(result, FaceRecognitionError):
            MessagePopup(title='FR Error', message=result.message).open()
            if result in (FaceRecognitionError.CAMERA_ERROR,
                          FaceRecognitionError.CAMERA_DISCONNECTED):
                self.camera_ready = False
            callback(None)
        elif isinstance(result, (list, tuple)) and result:
            name = str(result[0])
            MessagePopup(title='Detected', message=f'Detected: {name}').open()
            callback(name)
        else:
            MessagePopup(title='Face Recognition', message='No known face detected.').open()
            callback(None)

    # --- User actions ---
    def show_search_keyboard(self):
        VirtualKeyboardPopup(
            prompt='Search terms:',
            initial_text=self.ids.search_input.text,
            callback=lambda val: self._set_search(val),
        ).open()

    def _set_search(self, val):
        if val is not None:
            self.ids.search_input.text = val

    def log_item_use(self):
        self.scan_face('log item use', self._on_log_face)

    def _on_log_face(self, user):
        if not user:
            return
        ChoicePopup(callback=lambda choice: self._on_log_choice(choice, user)).open()

    def _on_log_choice(self, choice, user):
        if choice == 'restock':
            self._restock(user)
        elif choice == 'use':
            self._use_item(user)

    def _restock(self, user):
        InputPopup(
            title='Scan Barcode', prompt='Scan barcode:',
            callback=lambda bc: self._do_restock(bc, user),
        ).open()

    def _do_restock(self, barcode, user):
        if not barcode:
            return
        InputPopup(
            title='Location', prompt='Enter location:',
            callback=lambda loc: self._finish_restock(barcode, user, loc or 'default'),
        ).open()

    def _finish_restock(self, barcode, user, location):
        result = self.db.add_to_inventory(barcode, user, location)
        if result == LookupError:
            MessagePopup(title='Error', message=f'No drug found: {barcode}').open()
        elif result == IndexError:
            MessagePopup(title='Error', message=f'{barcode} already in inventory.').open()
        elif result is not None:
            MessagePopup(title='Error', message=f'Database error: {result}').open()
        else:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            MessagePopup(title='Logged', message=f'Restocked {barcode} at {now} by {user}').open()
            self.load_data()

    def _use_item(self, user):
        InputPopup(
            title='Scan Barcode', prompt='Scan item barcode:',
            callback=lambda bc: self._on_use_barcode(bc, user),
        ).open()

    def _on_use_barcode(self, barcode, user):
        if not barcode:
            return
        exists = self.db.check_if_barcode_exists(barcode)
        if not exists:
            MessagePopup(title='Invalid', message=f'Barcode {barcode} not found.').open()
            return
        drug_name = exists[1]
        InputPopup(
            title='Amount', prompt='Enter amount used:',
            validate_number=True,
            callback=lambda amt: self._do_use(drug_name, amt, user),
        ).open()

    def _do_use(self, drug_name, amount_str, user):
        if not amount_str:
            return
        amount = int(float(amount_str)) * -1
        try:
            self.db.log_access_to_inventory(barcode=drug_name, change=amount, user=user)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            MessagePopup(title='Used',
                         message=f'Logged {amount_str} of {drug_name}\nat {now} by {user}').open()
            self.load_data()
        except Exception as e:
            MessagePopup(title='Error', message=str(e)).open()

    def personal_run(self):
        self.scan_face('access personal DB', self._on_personal_face)

    def _on_personal_face(self, user):
        if not user:
            return
        personal = self.manager.get_screen('personal')
        personal.set_user(user)
        self.manager.current = 'personal'

    def delete_selected(self):
        self._admin_auth(self._do_delete)

    def _do_delete(self):
        body = self.ids.table_body
        selected = [w for w in body.children if isinstance(w, DataRow) and w.selected]
        if not selected:
            MessagePopup(title='Delete', message='No row selected.').open()
            return
        VirtualKeyboardPopup(
            title='Reason', prompt='Enter reason for deletion:',
            callback=lambda reason: self._confirm_delete(selected, reason),
        ).open()

    def _confirm_delete(self, selected, reason):
        if not reason or not reason.strip():
            MessagePopup(title='Error', message='A deletion reason is required.').open()
            return
        ConfirmPopup(
            title='Confirm Delete',
            message=f'Delete {len(selected)} row(s)?\nReason: {reason}',
            callback=lambda yes: self._execute_delete(selected, reason) if yes else None,
        ).open()

    def _execute_delete(self, selected, reason):
        try:
            for row in selected:
                barcode = row.row_data[1] if len(row.row_data) > 1 else row.row_data[0]
                self.db.delete_entry(barcode=barcode, reason=reason)
            self.load_data()
            MessagePopup(title='Deleted', message=f'Deleted {len(selected)} row(s).').open()
        except Exception as e:
            MessagePopup(title='Error', message=str(e)).open()

    def show_history(self):
        self._admin_auth(self._go_history)

    def _go_history(self):
        history = self.manager.get_screen('history')
        history.load_data()
        self.manager.current = 'history'

    def _admin_auth(self, on_success):
        InputPopup(
            title='Admin Auth', prompt='Enter admin code:',
            is_password=True,
            callback=lambda val: self._check_admin(val, on_success),
        ).open()

    def _check_admin(self, val, on_success):
        if val is None:
            return
        if str(val) == ADMIN_CODE:
            on_success()
        else:
            MessagePopup(title='Denied', message='Incorrect admin code.').open()


class HistoryScreen(Screen):
    """History / change log screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        Clock.schedule_once(self._build_header, 0)

    HIST_COLS = ['Barcode', 'Name', 'Amt Changed', 'User', 'Type', 'Time', 'Reason']

    def _build_header(self, dt):
        header = self.ids.hist_header
        header.clear_widgets()
        for col in self.HIST_COLS:
            lbl = Label(text=col, font_size=dp(14), bold=True,
                        halign='left', valign='middle')
            lbl.bind(size=lbl.setter('text_size'))
            header.add_widget(lbl)

    def load_data(self):
        body = self.ids.hist_body
        body.clear_widgets()
        try:
            rows = self.db.pull_data("drug_changes")
            for row in rows:
                body.add_widget(DataRow(row))
        except Exception as e:
            print(f"History load error: {e}")

    def show_pattern_rec(self):
        try:
            result = self.db.pattern_recognition()
            MessagePopup(title='Pattern Recognition', message=str(result)).open()
        except Exception as e:
            MessagePopup(title='Error', message=str(e)).open()

    def go_back(self):
        self.manager.current = 'main'


class PersonalScreen(Screen):
    """Personal database screen with prescription/history tables."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = ''
        self.current_date = datetime.date.today()
        self.db = DatabaseManager()
        self.personal_db = None

    def set_user(self, user):
        self.user = user
        self.ids.title_label.text = f"{user}'s Personal Database"
        try:
            self.personal_db = PersonalDatabaseManager(user)
        except Exception as e:
            print(f"Personal DB error: {e}")
            self.personal_db = None
        self.current_date = datetime.date.today()
        self.load_data()

    def load_data(self):
        self.ids.date_label.text = self.current_date.strftime("%A, %B %d, %Y")
        self._load_prescriptions()
        self._load_history()
        self._load_as_needed()

    def _load_prescriptions(self):
        body = self.ids.presc_body
        body.clear_widgets()
        if not self.personal_db:
            return
        try:
            _, raw = self.personal_db.get_personal_data(self.current_date)
            body.add_widget(DataRow(['Name', 'Dose', 'Time', 'Leeway', 'As Needed']))
            for p in raw:
                if len(p) < 6:
                    continue
                if p[5] in (True, 1, "True"):
                    continue  # shown in as-needed section
                body.add_widget(DataRow([p[1], p[2], str(p[3] or '-'), str(p[4] or '-'), 'No']))
        except Exception as e:
            print(f"Prescription load error: {e}")

    def _load_history(self):
        body = self.ids.hist_body
        body.clear_widgets()
        if not self.personal_db:
            return
        try:
            raw, _ = self.personal_db.get_personal_data(self.current_date)
            body.add_widget(DataRow(['Name', 'Time', 'Amount', 'Matched']))
            for h in raw:
                if len(h) < 5:
                    continue
                matched = chr(0x2713) if h[4] else chr(0x2014)
                body.add_widget(DataRow([h[1], str(h[2] or '-'), str(h[3]), matched]))
        except Exception as e:
            print(f"History load error: {e}")

    def _load_as_needed(self):
        body = self.ids.as_needed_body
        body.clear_widgets()
        if not self.personal_db:
            return
        try:
            _, raw = self.personal_db.get_personal_data(self.current_date)
            for p in raw:
                if len(p) < 6:
                    continue
                if p[5] in (True, 1, "True"):
                    body.add_widget(DataRow([f"  {p[1]}", f"Dose: {p[2]}"]))
        except Exception as e:
            print(f"As-needed load error: {e}")

    def previous_day(self):
        self.current_date -= datetime.timedelta(days=1)
        self.load_data()

    def next_day(self):
        self.current_date += datetime.timedelta(days=1)
        self.load_data()

    def goto_today(self):
        self.current_date = datetime.date.today()
        self.load_data()

    def use_item_from_personal(self):
        InputPopup(
            title='Scan Barcode', prompt='Scan item barcode:',
            callback=self._on_personal_barcode,
        ).open()

    def _on_personal_barcode(self, barcode):
        if not barcode:
            return
        exists = self.db.check_if_barcode_exists(barcode)
        if not exists:
            MessagePopup(title='Invalid', message=f'Barcode {barcode} not found.').open()
            return
        drug_name = exists[1]
        InputPopup(
            title='Amount', prompt='Enter amount used:',
            validate_number=True,
            callback=lambda amt: self._do_personal_use(drug_name, amt),
        ).open()

    def _do_personal_use(self, drug_name, amount_str):
        if not amount_str:
            return
        amount = int(float(amount_str)) * -1
        try:
            self.db.log_access_to_inventory(barcode=drug_name, change=amount, user=self.user)
            MessagePopup(title='Used', message=f'Logged usage of {drug_name}').open()
            self.load_data()
        except Exception as e:
            MessagePopup(title='Error', message=str(e)).open()

    def go_back(self):
        self.manager.current = 'main'


# ============================================================================
# APP
# ============================================================================

class MedicalInventoryApp(App):
    title = 'Medical Inventory System'

    def build(self):
        Window.clearcolor = (0.11, 0.11, 0.12, 1)
        try:
            Window.fullscreen = 'auto'
        except Exception:
            Window.size = (1280, 800)

        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(HistoryScreen(name='history'))
        sm.add_widget(PersonalScreen(name='personal'))
        return sm


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    MedicalInventoryApp().run()
