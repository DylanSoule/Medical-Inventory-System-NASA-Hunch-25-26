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
    """Displays the recent drug-change history table.

    Responsibilities
    ----------------
    * Render the last 7 days of inventory changes.
    * Run and display pattern-recognition anomaly results.
    * Navigate back to the main screen.
    """

    HIST_COLS = ['Barcode', 'Name', 'Amt Changed', 'User', 'Type', 'Time', 'Reason']

    # ================================================================== #
    # region           INITIALISATION                                     #
    # ================================================================== #

    def __init__(self, **kwargs):
        """Create the DB handle and schedule the header build."""
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        Clock.schedule_once(self._build_header, 0)

    # endregion

    # ================================================================== #
    # region           TABLE HEADER & DATA                                #
    # ================================================================== #

    def _build_header(self, dt):
        """Populate the header row with column labels from HIST_COLS."""
        header = self.ids.hist_header
        header.clear_widgets()
        for col in self.HIST_COLS:
            lbl = Label(text=col, font_size=dp(14), bold=True,
                        halign='left', valign='middle')
            lbl.bind(size=lbl.setter('text_size'))
            header.add_widget(lbl)

    def load_data(self):
        """Fetch recent change rows from the DB and add them to the table."""
        body = self.ids.hist_body
        body.clear_widgets()
        try:
            rows = self.db.pull_data("drug_changes")
            for row in rows:
                body.add_widget(DataRow(row))
        except Exception as e:
            print(f"History load error: {e}")

    # endregion

    # ================================================================== #
    # region           PATTERN RECOGNITION                                #
    # ================================================================== #

    def show_pattern_rec(self):
        """Run the anomaly-detection algorithm and show results in a popup."""
        try:
            result = self.db.pattern_recognition()
            MessagePopup(title='Pattern Recognition', message=str(result)).open()
        except Exception as e:
            MessagePopup(title='Error', message=str(e)).open()

    # endregion

    # ================================================================== #
    # region           NAVIGATION                                         #
    # ================================================================== #

    def go_back(self):
        """Return to the main inventory screen."""
        self.manager.current = 'main'

    # endregion
