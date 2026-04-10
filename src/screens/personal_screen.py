"""
Medical Inventory System - Personal Database Screen

Per-user view: scheduled prescriptions, usage history,
as-needed medications, and day navigation.
"""

import datetime

from kivy.uix.screenmanager import Screen

from database import DatabaseManager, PersonalDatabaseManager
from widgets import MessagePopup, InputPopup, DataRow


class PersonalScreen(Screen):
    """Per-user screen showing prescriptions, history, and as-needed meds.

    Responsibilities
    ----------------
    * Show scheduled prescriptions for the active user.
    * Show daily usage history with prescription-match indicators.
    * List as-needed medications separately.
    * Navigate between days and log usage from this view.
    """

    # ================================================================== #
    # region           INITIALISATION                                     #
    # ================================================================== #

    def __init__(self, **kwargs):
        """Set up DB handles and default state."""
        super().__init__(**kwargs)
        self.user = ''
        self.current_date = datetime.date.today()
        self.db = DatabaseManager()
        self.personal_db = None

    # endregion

    # ================================================================== #
    # region           USER SETUP                                         #
    # ================================================================== #

    def set_user(self, user):
        """Initialise the screen for *user* — creates a PersonalDatabaseManager
        and loads today's data.

        Parameters
        ----------
        user : str
            The name returned by facial recognition.
        """
        self.user = user
        self.ids.title_label.text = f"{user}'s Personal Database"
        try:
            self.personal_db = PersonalDatabaseManager(user)
        except Exception as e:
            print(f"Personal DB error: {e}")
            self.personal_db = None
        self.current_date = datetime.date.today()
        self.load_data()

    # endregion

    # ================================================================== #
    # region           DATA LOADING                                       #
    # ================================================================== #

    def load_data(self):
        """Refresh all three sub-tables for ``self.current_date``."""
        self.ids.date_label.text = self.current_date.strftime("%A, %B %d, %Y")
        self._load_prescriptions()
        self._load_history()
        self._load_as_needed()

    def _load_prescriptions(self):
        """Populate the scheduled-prescriptions table (excludes as-needed)."""
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
        """Populate the usage-history table with match indicators."""
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
        """Populate the as-needed medication list."""
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

    # endregion

    # ================================================================== #
    # region           DAY NAVIGATION                                     #
    # ================================================================== #

    def previous_day(self):
        """Move to the previous calendar day and reload."""
        self.current_date -= datetime.timedelta(days=1)
        self.load_data()

    def next_day(self):
        """Move to the next calendar day and reload."""
        self.current_date += datetime.timedelta(days=1)
        self.load_data()

    def goto_today(self):
        """Jump back to today and reload."""
        self.current_date = datetime.date.today()
        self.load_data()

    # endregion

    # ================================================================== #
    # region           USE ITEM FROM PERSONAL VIEW                        #
    # ================================================================== #

    def use_item_from_personal(self):
        """Step 1 — prompt for the item barcode."""
        InputPopup(
            title='Scan Barcode', prompt='Scan item barcode:',
            callback=self._on_personal_barcode,
        ).open()

    def _on_personal_barcode(self, barcode):
        """Step 2 — validate barcode exists, then prompt for amount."""
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
        """Step 3 — log the negative amount change and refresh."""
        if not amount_str:
            return
        amount = int(float(amount_str)) * -1
        try:
            self.db.log_access_to_inventory(barcode=drug_name, change=amount, user=self.user)
            MessagePopup(title='Used', message=f'Logged usage of {drug_name}').open()
            self.load_data()
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
