"""
Medical Inventory System - Reusable Kivy Widgets

Popups, numpad, data-row, header-row, virtual keyboard.
Every screen imports from here — single source of truth (DRY).
"""

from kivy.clock import Clock
from kivy.properties import (
    StringProperty, ListProperty, BooleanProperty, ObjectProperty
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp


# ============================================================================
# NUMPAD
# ============================================================================

class NumpadWidget(GridLayout):
    """Reusable numpad grid. Dispatches 'on_key' with the key character."""

    _KEYS = ['7', '8', '9', '4', '5', '6', '1', '2', '3', 'C', '0', '<']

    def __init__(self, **kwargs):
        self.register_event_type('on_key')
        super().__init__(**kwargs)
        self._build()

    def _build(self):
        self.clear_widgets()
        for k in self._KEYS:
            btn = Button(
                text=k, font_size=dp(22),
                background_normal='',
                background_color=(0.25, 0.25, 0.28, 1),
            )
            btn.bind(on_release=lambda inst, key=k: self.dispatch('on_key', key))
            self.add_widget(btn)

    def on_key(self, *args):
        pass


# ============================================================================
# POPUPS
# ============================================================================

class MessagePopup(Popup):
    """Simple message popup with OK button."""
    message = StringProperty('')

    def __init__(self, title='Info', message='', **kwargs):
        super().__init__(title=title, **kwargs)
        self.message = message


class ConfirmPopup(Popup):
    """Yes / No confirmation popup."""
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
