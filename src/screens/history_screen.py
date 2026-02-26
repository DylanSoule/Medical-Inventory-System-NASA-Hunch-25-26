"""
Medical Inventory System - History Screen

Shows the change-log / history table and pattern recognition.
"""

from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp

from database import DatabaseManager
from widgets import MessagePopup, DataRow


class HistoryScreen(Screen):
    """History / change-log screen."""

    HIST_COLS = ['Barcode', 'Name', 'Amt Changed', 'User', 'Type', 'Time', 'Reason']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        Clock.schedule_once(self._build_header, 0)

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
