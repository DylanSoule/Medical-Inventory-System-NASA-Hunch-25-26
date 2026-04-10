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
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle

# ====================================================================== #
# region           NUMPAD WIDGET                                          #
# ====================================================================== #

class NumpadWidget(GridLayout):
    """Reusable 3×4 numeric keypad. Dispatches ``on_key`` with the character.

    Keys: 0-9, C (clear), < (backspace).
    """

    _KEYS = ['7', '8', '9', '4', '5', '6', '1', '2', '3', 'C', '0', '<']

    def __init__(self, **kwargs):
        """Register the custom ``on_key`` event and build the buttons."""
        self.register_event_type('on_key')
        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Create a Button for every key and wire it to ``on_key``."""
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
        """Default handler — overridden by listeners."""
        pass

# endregion


# ====================================================================== #
# region           MESSAGE POPUP                                          #
# ====================================================================== #

class MessagePopup(Popup):
    """Simple informational popup with a single OK button.

    Parameters
    ----------
    title : str
        Popup window title.
    message : str
        Body text displayed to the user.
    """
    message = StringProperty('')

    def __init__(self, title='Info', message='', **kwargs):
        super().__init__(title=title, **kwargs)
        self.message = message

# endregion


# ====================================================================== #
# region           CONFIRM POPUP                                          #
# ====================================================================== #

class ConfirmPopup(Popup):
    """Yes / No confirmation popup.

    Parameters
    ----------
    title : str
        Popup window title.
    message : str
        Question text.
    callback : callable(bool) or None
        Called with True (Yes) or False (No).
    """
    message = StringProperty('')
    callback = ObjectProperty(None, allownone=True)

    def __init__(self, title='Confirm', message='', callback=None, **kwargs):
        super().__init__(title=title, **kwargs)
        self.message = message
        self.callback = callback

    def on_yes(self):
        """User pressed Yes — invoke callback(True) and dismiss."""
        if self.callback:
            self.callback(True)
        self.dismiss()

    def on_no(self):
        """User pressed No — invoke callback(False) and dismiss."""
        if self.callback:
            self.callback(False)
        self.dismiss()

# endregion


# ====================================================================== #
# region           INPUT POPUP                                            #
# ====================================================================== #

class InputPopup(Popup):
    """Modal text/number input with an embedded numpad.

    Calls ``callback(value)`` on OK, ``callback(None)`` on Cancel.

    Parameters
    ----------
    prompt : str
        Label text above the input field.
    is_password : bool
        Mask input characters if True.
    validate_number : bool
        If True, reject non-numeric input on OK.
    """
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
        """Handle a key press from the embedded NumpadWidget."""
        if key == 'C':
            self.input_text = ''
        elif key == '<':
            self.input_text = self.input_text[:-1]
        else:
            self.input_text += key

    def on_ok(self):
        """Validate and return the entered value via callback."""
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
        """Return None via callback and close."""
        if self.callback:
            self.callback(None)
        self.dismiss()

# endregion


# ====================================================================== #
# region           CHOICE POPUP                                           #
# ====================================================================== #

class ChoicePopup(Popup):
    """Three-button chooser: Restock / Use Item / Cancel.

    Parameters
    ----------
    callback : callable(str | None) or None
        Called with ``'restock'``, ``'use'``, or ``None``.
    """
    callback = ObjectProperty(None, allownone=True)

    def __init__(self, callback=None, **kwargs):
        super().__init__(title='Log Item Use', **kwargs)
        self.callback = callback

    def choose(self, choice):
        """Dispatch the user's choice and dismiss."""
        if self.callback:
            self.callback(choice)
        self.dismiss()

# endregion


# ====================================================================== #
# region           VIRTUAL KEYBOARD POPUP                                 #
# ====================================================================== #

class VirtualKeyboardPopup(Popup):
    """Full QWERTY virtual keyboard popup for touch-only environments.

    Parameters
    ----------
    prompt : str
        Label text above the input field.
    initial_text : str
        Pre-filled input content.
    callback : callable(str | None) or None
        Called with the final text on OK, or None on Cancel.
    """
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
        """Dynamically generate key-rows and the bottom action bar."""
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

    # -- Internal key handlers --

    def _key_press(self, key):
        """Append the character (upper-cased if Shift is active)."""
        ch = key.upper() if self._shift else key
        self.input_text += ch
        if self._shift:
            self._shift = False

    def _toggle_shift(self):
        """Toggle the Shift flag for the next character."""
        self._shift = not self._shift

    def _backspace(self):
        """Remove the last character."""
        self.input_text = self.input_text[:-1]

    def _clear(self):
        """Clear all input text."""
        self.input_text = ''

    # -- OK / Cancel --

    def on_ok(self):
        """Return the trimmed text via callback and dismiss."""
        if self.callback:
            self.callback(self.input_text.strip())
        self.dismiss()

    def on_cancel(self):
        """Return None via callback and dismiss."""
        if self.callback:
            self.callback(None)
        self.dismiss()

# endregion


# ====================================================================== #
# region           TABLE ROWS                                             #
# ====================================================================== #

class DataRow(BoxLayout):
    """A single selectable data row in the inventory table.

    Attributes
    ----------
    selected : BooleanProperty
        Toggles on touch; drives the highlight colour in KV.
    row_data : ListProperty
        The full raw values for this row (may exceed visible columns).
    """
    selected = BooleanProperty(False)
    row_data = ListProperty([])

    def __init__(self, row_data, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(36)
        self.selected = False
        self.row_data = list(row_data)

        for i, val in enumerate(row_data):
            if i > 0:
                self.add_widget(self._column_separator())
            lbl = Label(text=str(val), font_size=dp(14), halign='left', valign='middle', padding=(dp(4), 0))
            lbl.bind(size=lbl.setter('text_size'))
            self.add_widget(lbl)

    def on_touch_down(self, touch):
        """Toggle selection when the row is tapped."""
        if self.collide_point(*touch.pos):
            self.selected = not self.selected
            return True
        return super().on_touch_down(touch)

    @staticmethod
    def _column_separator():
        """Return a thin vertical line widget to visually separate columns."""
        sep = Widget(size_hint_x=None, width=dp(1))
        with sep.canvas:
            Color(1, 1, 1, 0.15)
            sep._rect = Rectangle(pos=sep.pos, size=sep.size)
        sep.bind(pos=lambda w, p: setattr(w._rect, 'pos', p),
                 size=lambda w, s: setattr(w._rect, 'size', s))
        return sep

class HeaderRow(BoxLayout):
    """Column header row — styled via KV, populated programmatically."""
    pass

# endregion
    pass
