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

import facial_recognition as fr
from database import DatabaseManager
from facial_recognition import FaceRecognitionError
from constants import COLUMNS, REFRESH_INTERVAL, ADMIN_CODE
from widgets import (
    MessagePopup, ConfirmPopup, InputPopup,
    ChoicePopup, VirtualKeyboardPopup, DataRow,
)


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

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------
    def _init_ui(self, dt):
        self._build_header()
        self._build_column_checkboxes()
        self._start_preloading()
        self._start_camera_monitor()
        self.load_data()
        Clock.schedule_interval(lambda dt: self.load_data(), REFRESH_INTERVAL)

    # ------------------------------------------------------------------
    # Column checkboxes
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    def _build_header(self):
        header = self.ids.header_row
        header.clear_widgets()
        for col_id, label, _ in COLUMNS:
            if self.visible_columns.get(col_id, True):
                lbl = Label(text=label, font_size=dp(15), bold=True,
                            halign='left', valign='middle')
                lbl.bind(size=lbl.setter('text_size'))
                header.add_widget(lbl)

    # ------------------------------------------------------------------
    # Data loading & filtering
    # ------------------------------------------------------------------
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

            # Expiration filter
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

    # ------------------------------------------------------------------
    # Facial recognition helpers
    # ------------------------------------------------------------------
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
        """Run face recognition in background, then call callback(name) on main thread."""
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

    # ------------------------------------------------------------------
    # User actions
    # ------------------------------------------------------------------
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

    # -- Restock flow --
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

    # -- Use item flow --
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

    # -- Personal DB --
    def personal_run(self):
        self.scan_face('access personal DB', self._on_personal_face)

    def _on_personal_face(self, user):
        if not user:
            return
        personal = self.manager.get_screen('personal')
        personal.set_user(user)
        self.manager.current = 'personal'

    # -- Delete --
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

    # -- History --
    def show_history(self):
        self._admin_auth(self._go_history)

    def _go_history(self):
        history = self.manager.get_screen('history')
        history.load_data()
        self.manager.current = 'history'

    # -- Admin auth (shared helper) --
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
