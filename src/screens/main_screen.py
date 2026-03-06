"""
Medical Inventory System - Main Inventory Screen

Handles the data table, searching, filtering, barcode scanning,
facial-recognition gates, and admin actions.
"""

import datetime
import threading
import time

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle

import facial_recognition as fr
from database import DatabaseManager
from facial_recognition import FaceRecognitionError
from constants import COLUMNS, REFRESH_INTERVAL, ADMIN_CODE
from widgets import (
    MessagePopup, ConfirmPopup, InputPopup,
    ChoicePopup, VirtualKeyboardPopup, DataRow,
)


class MainScreen(Screen):
    """Primary screen — inventory data-table with sidebar controls."""

    # ================================================================== #
    # region           INITIALIZATION                                     #
    # ================================================================== #

    def __init__(self, **kwargs):
        """Set up DB handle, empty row cache, FR flags, and schedule UI init."""
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self._all_rows = []
        self.fr_ready = False
        self.camera_ready = False
        self.visible_columns = {col_id: True for col_id, _, _ in COLUMNS}
        self._filter_trigger = None
        self._last_row_hash = None
        self._row_cache = {}
        self._current_keys = []           # ordered keys of currently shown rows
        Clock.schedule_once(self._init_ui, 0)

    def _init_ui(self, dt):
        """Called once after the KV tree is built — wire up everything."""
        if not self.ids:
            Clock.schedule_once(self._init_ui, 0.1)
            return
        self._build_column_checkboxes()
        self._build_header()
        self._start_preloading()
        self._start_camera_monitor()
        self.load_data()
        Clock.schedule_interval(self._bg_load_data, REFRESH_INTERVAL)

    # endregion

    # ================================================================== #
    # region           TABLE HEADER & COLUMN TOGGLES                      #
    # ================================================================== #

    def _build_column_checkboxes(self):
        """Populate the column_filters bar with checkbox+label pairs."""
        column_filters = self.ids.column_filters
        column_filters.clear_widgets()

        for col_id, label, _ in COLUMNS:
            pair = BoxLayout(orientation='horizontal', size_hint_x=1, spacing=dp(4))

            cb = CheckBox(active=True, size_hint_x=None, width=dp(28))
            cb.bind(active=lambda inst, val, cid=col_id: self._toggle_column(cid, val))

            lbl = Label(
                text=label, font_size=dp(13), bold=True,
                halign='left', valign='middle',
                size_hint_x=0.75, padding=(dp(2), 0),
            )
            lbl.bind(size=lbl.setter('text_size'))

            pair.add_widget(cb)
            pair.add_widget(lbl)
            column_filters.add_widget(pair)
            column_filters.add_widget(MainScreen._column_separator())

    def _toggle_column(self, col_id, visible):
        """Show or hide a column — just toggles size/opacity, no widget tree changes."""
        self.visible_columns[col_id] = visible
        self._build_header()
        self._update_row_displays()

    def _build_header(self):
        """Rebuild the header row labels based on current column visibility."""
        header = self.ids.header_row
        header.clear_widgets()
        visible = [(col_id, label) for col_id, label, _ in COLUMNS
                    if self.visible_columns.get(col_id, True)]
        for i, (col_id, label) in enumerate(visible):
            if i > 0:
                header.add_widget(self._column_separator())
            lbl = Label(
                text=label, font_size=dp(15), bold=True,
                halign='left', valign='middle', padding=(dp(4), 0),
            )
            lbl.bind(size=lbl.setter('text_size'))
            header.add_widget(lbl)

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

    # endregion

    # ================================================================== #
    # region           DATA LOADING & FILTERING                           #
    # ================================================================== #

    def load_data(self):
        """Synchronous initial load (called once at startup and after mutations)."""
        try:
            self._all_rows = list(self.db.pull_data("drugs_in_inventory"))
        except Exception as e:
            print(f"Error loading data: {e}")
            self._all_rows = []
        self._last_row_hash = hash(tuple(tuple(r) for r in self._all_rows))
        self._row_cache.clear()
        self._current_keys = []
        self._sync_cache()
        self._apply_filters_now()

    def _bg_load_data(self, dt):
        """Pull data from DB in a background thread to avoid blocking the UI."""
        def worker():
            try:
                rows = list(self.db.pull_data("drugs_in_inventory"))
            except Exception as e:
                print(f"Error loading data: {e}")
                rows = []

            row_hash = hash(tuple(tuple(r) for r in rows))
            if row_hash == self._last_row_hash:
                return
            self._last_row_hash = row_hash

            def update(dt):
                self._all_rows = rows
                self._row_cache.clear()
                self._current_keys = []
                self._sync_cache()
                self._apply_filters_now()

            Clock.schedule_once(update, 0)

        threading.Thread(target=worker, daemon=True).start()

    def _sync_cache(self):
        """Create DataRow widgets with ALL column labels pre-attached."""
        for row in self._all_rows:
            try:
                drug, barcode, est_amount = row[0], row[1], row[2]
                exp_date_raw, type_, dose_size, item_loc = row[3], row[4], row[5], row[6]
            except (IndexError, ValueError):
                continue

            full = (type_, drug, barcode, est_amount, exp_date_raw, dose_size, item_loc)
            key = (barcode, drug)

            if key not in self._row_cache:
                dr = DataRow(())
                dr.row_data = list(full)
                dr._full = full
                dr._col_labels = {}
                dr._col_seps = {}

                for i, (cid, _, _) in enumerate(COLUMNS):
                    lbl = Label(
                        text=str(full[i]),
                        font_size=dp(14),
                        halign='left',
                        valign='middle',
                        padding=(dp(4), 0),
                    )
                    lbl.bind(size=lbl.setter('text_size'))
                    dr._col_labels[cid] = lbl
                    dr._col_seps[cid] = self._column_separator()

                    dr.add_widget(dr._col_seps[cid])
                    dr.add_widget(lbl)

                # Remove the first separator (no separator before first column)
                first_cid = COLUMNS[0][0]
                dr.remove_widget(dr._col_seps[first_cid])

                self._row_cache[key] = dr

        self._update_row_displays()

    def _update_row_displays(self):
        """Show/hide individual labels and separators using size + opacity.
        No add_widget / remove_widget / clear_widgets calls."""
        for dr in self._row_cache.values():
            first_visible = True
            for cid, _, _ in COLUMNS:
                lbl = dr._col_labels[cid]
                sep = dr._col_seps[cid]
                visible = self.visible_columns.get(cid, True)

                if visible:
                    lbl.size_hint_x = 1
                    lbl.opacity = 1
                    if first_visible:
                        sep.size_hint_x = None
                        sep.width = 0
                        sep.opacity = 0
                        first_visible = False
                    else:
                        sep.size_hint_x = None
                        sep.width = dp(1)
                        sep.opacity = 1
                else:
                    lbl.size_hint_x = None
                    lbl.width = 0
                    lbl.opacity = 0
                    sep.size_hint_x = None
                    sep.width = 0
                    sep.opacity = 0

    def _schedule_filter(self, *args):
        """Debounce filter requests — wait 0.1s of inactivity before rebuilding."""
        if self._filter_trigger:
            self._filter_trigger.cancel()
        self._filter_trigger = Clock.schedule_once(
            lambda dt: self._apply_filters_now(), 0.1
        )

    def apply_filters(self, *args):
        """Public entry point for KV bindings — debounced."""
        self._schedule_filter()

    def _apply_filters_now(self):
        """Rebuild the visible row list. Only touches the widget tree when
        the set or order of visible rows has actually changed."""
        body = self.ids.table_body

        query = self.ids.search_input.text.strip().lower()
        mode = self.ids.filter_spinner.text
        low_only = self.ids.low_stock_cb.active
        now = datetime.date.today()

        to_show_keys = []

        for row in self._all_rows:
            try:
                drug, barcode, est_amount = row[0], row[1], row[2]
                exp_date_raw, type_, dose_size, item_loc = row[3], row[4], row[5], row[6]
            except (IndexError, ValueError):
                continue

            key = (barcode, drug)
            if key not in self._row_cache:
                continue

            # --- search filter ---
            if query:
                fields = [str(v).lower() for v in (type_, drug, barcode, dose_size, item_loc)]
                if not any(query in f for f in fields):
                    continue

            # --- low-stock filter ---
            if low_only:
                try:
                    if float(est_amount) > 20:
                        continue
                except (ValueError, TypeError):
                    continue

            # --- expiration filter ---
            if mode != 'All':
                exp_date = self._parse_date(exp_date_raw)
                if mode == "Expired":
                    if not exp_date or exp_date >= now:
                        continue
                elif mode == "Expiring Soon":
                    if not exp_date:
                        continue
                    delta = (exp_date - now).days
                    if delta < 0 or delta > 30:
                        continue

            to_show_keys.append(key)

        # Sort by type (first column) alphabetically
        to_show_keys.sort(key=lambda k: str(self._row_cache[k]._full[0]).lower())

        # --- Skip rebuild if nothing changed ---
        if to_show_keys == self._current_keys:
            return

        # --- Swap entire body at once ---
        body.clear_widgets()
        for key in to_show_keys:
            body.add_widget(self._row_cache[key])
        self._current_keys = to_show_keys

    @staticmethod
    def _parse_date(d):
        """Try common date formats and return a ``datetime.date`` or None."""
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

    # endregion

    # ================================================================== #
    # region           FACIAL RECOGNITION                                 #
    # ================================================================== #

    def _start_preloading(self):
        """Spin up a daemon thread that loads the FR model + reference embeddings."""
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
        """Daemon thread that retries camera init with exponential back-off."""
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
        """Run face recognition in a background thread.

        Parameters
        ----------
        purpose : str
            Human-readable label (unused, kept for future logging).
        callback : callable(name: str | None)
            Called on the main thread with the detected name, or None.
        """
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
        """Interpret the FR return value and invoke *callback* with the name or None."""
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

    # endregion

    # ================================================================== #
    # region           SEARCH                                             #
    # ================================================================== #

    def show_search_keyboard(self):
        """Open the virtual keyboard pre-filled with the current search text."""
        VirtualKeyboardPopup(
            prompt='Search terms:', 
            initial_text=self.ids.search_input.text,
            callback=lambda val: self._set_search(val),
        ).open()

    def _set_search(self, val):
        """Apply the keyboard result back to the search TextInput."""
        if val is not None:
            self.ids.search_input.text = val

    # endregion

    # ================================================================== #
    # region           LOG ITEM USE (entry point → choice → flow)         #
    # ================================================================== #

    def log_item_use(self):
        """Gate behind FR, then present the Restock / Use choice."""
        self.scan_face('log item use', self._on_log_face)

    def _on_log_face(self, user):
        """FR callback — open the choice popup if a face was detected."""
        if not user:
            return
        ChoicePopup(callback=lambda choice: self._on_log_choice(choice, user)).open()

    def _on_log_choice(self, choice, user):
        """Route the user's choice to the correct workflow."""
        if choice == 'restock':
            self._restock(user)
        elif choice == 'use':
            self._use_item(user)

    # endregion

    # ================================================================== #
    # region           RESTOCK FLOW                                       #
    # ================================================================== #

    def _restock(self, user):
        """Step 1 — prompt for a barcode to restock."""
        InputPopup(
            title='Scan Barcode', prompt='Scan barcode:',
            callback=lambda bc: self._do_restock(bc, user),
        ).open()

    def _do_restock(self, barcode, user):
        """Step 2 — prompt for the storage location."""
        if not barcode:
            return
        InputPopup(
            title='Location', prompt='Enter location:',
            callback=lambda loc: self._finish_restock(barcode, user, loc or 'default'),
        ).open()

    def _finish_restock(self, barcode, user, location):
        """Step 3 — write to DB and show success / error feedback."""
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

    # endregion

    # ================================================================== #
    # region           USE ITEM FLOW                                      #
    # ================================================================== #

    def _use_item(self, user):
        """Step 1 — prompt for the item barcode."""
        InputPopup(
            title='Scan Barcode', prompt='Scan item barcode:',
            callback=lambda bc: self._on_use_barcode(bc, user),
        ).open()

    def _on_use_barcode(self, barcode, user):
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
            callback=lambda amt: self._do_use(drug_name, amt, user),
        ).open()

    def _do_use(self, drug_name, amount_str, user):
        """Step 3 — log the negative amount change and refresh the table."""
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

    # endregion

    # ================================================================== #
    # region           PERSONAL DATABASE                                  #
    # ================================================================== #

    def personal_run(self):
        """Gate behind FR, then navigate to the PersonalScreen."""
        self.scan_face('access personal DB', self._on_personal_face)

    def _on_personal_face(self, user):
        """FR callback — switch to the personal screen for *user*."""
        if not user:
            return
        personal = self.manager.get_screen('personal')
        personal.set_user(user)
        self.manager.current = 'personal'

    # endregion

    # ================================================================== #
    # region           DELETE SELECTED ROWS                               #
    # ================================================================== #

    def delete_selected(self):
        """Gate behind admin auth, then start the delete flow."""
        self._admin_auth(self._do_delete)

    def _do_delete(self):
        """Collect selected rows and prompt for a deletion reason."""
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
        """Validate the reason, then show a Yes/No confirmation."""
        if not reason or not reason.strip():
            MessagePopup(title='Error', message='A deletion reason is required.').open()
            return
        ConfirmPopup(
            title='Confirm Delete',
            message=f'Delete {len(selected)} row(s)?\nReason: {reason}',
            callback=lambda yes: self._execute_delete(selected, reason) if yes else None,
        ).open()

    def _execute_delete(self, selected, reason):
        """Delete every selected row from the DB and refresh the table."""
        try:
            for row in selected:
                # row_data is (type_, drug, barcode, est_amt, exp_date, dose_size, location)
                barcode = row.row_data[2] if len(row.row_data) > 2 else row.row_data[0]
                self.db.delete_entry(barcode=barcode, reason=reason)
            self.load_data()
            MessagePopup(title='Deleted', message=f'Deleted {len(selected)} row(s).').open()
        except Exception as e:
            MessagePopup(title='Error', message=str(e)).open()

    # endregion

    # ================================================================== #
    # region           HISTORY NAVIGATION                                 #
    # ================================================================== #

    def show_history(self):
        """Gate behind admin auth, then navigate to the HistoryScreen."""
        self._admin_auth(self._go_history)

    def _go_history(self):
        """Load history data and switch to the history screen."""
        history = self.manager.get_screen('history')
        history.load_data()
        self.manager.current = 'history'

    # endregion

    # ================================================================== #
    # region           ADMIN AUTHENTICATION                               #
    # ================================================================== #

    def _admin_auth(self, on_success):
        """Show a password input; call *on_success()* only if code matches.

        Parameters
        ----------
        on_success : callable
            No-arg function invoked when the correct admin code is entered.
        """
        InputPopup(
            title='Admin Auth', prompt='Enter admin code:',
            is_password=True,
            callback=lambda val: self._check_admin(val, on_success),
        ).open()

    def _check_admin(self, val, on_success):
        """Compare *val* against ADMIN_CODE and proceed or deny."""
        if val is None:
            return
        if str(val) == ADMIN_CODE:
            on_success()
        else:
            MessagePopup(title='Denied', message='Incorrect admin code.').open()

    # endregion
