"""
Medical Inventory System - Kivy Implementation
NASA HUNCH Project 2025-26

This application manages medical inventory with barcode scanning,
facial recognition, and usage tracking using Kivy framework.
"""

import os
import sys
from datetime import datetime, timedelta
import threading
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.properties import StringProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.metrics import dp, sp

import facial_recognition as fr
from Database.database import DatabaseManager
from facial_recognition import FaceRecognitionError

# ============================================================================
# CONSTANTS
# ============================================================================

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Database/inventory.db")
REFRESH_INTERVAL = 30  # seconds

# Column configurations
COLUMNS = [
    {"id": "drug", "label": "Drug", "width": 220},
    {"id": "barcode", "label": "Barcode", "width": 170},
    {"id": "est_amount", "label": "Amt~", "width": 100},
    {"id": "exp_date", "label": "Expiration", "width": 140},
    {"id": "type_", "label": "Type", "width": 120},
    {"id": "dose_size", "label": "Dose Size", "width": 140},
    {"id": "item_type", "label": "Item Type", "width": 140},
    {"id": "item_loc", "label": "Location", "width": 100}
]

# ============================================================================
# CUSTOM WIDGETS
# ============================================================================

class DataRow(BoxLayout):
    """Custom widget for displaying a data row in the inventory table"""
    
    def __init__(self, data, columns_visible, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.spacing = dp(2)
        
        for col in COLUMNS:
            if columns_visible.get(col['id'], True):
                cell = Label(
                    text=str(data.get(col['id'], '')),
                    size_hint_x=None,
                    width=dp(col['width']),
                    color=(1, 1, 1, 1),
                    font_size=sp(14),
                    halign='left',
                    valign='middle',
                    text_size=(dp(col['width'] - 10), None)
                )
                cell.bind(size=cell.setter('text_size'))
                self.add_widget(cell)


class DataTable(ScrollView):
    """Custom scrollable data table widget"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.columns_visible = {col['id']: True for col in COLUMNS}
        
        # Create container for rows
        self.data_container = GridLayout(
            cols=1,
            spacing=dp(1),
            size_hint_y=None
        )
        self.data_container.bind(minimum_height=self.data_container.setter('height'))
        self.add_widget(self.data_container)
        
        # Create header
        self.create_header()
    
    def create_header(self):
        """Create table header"""
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(2)
        )
        
        for col in COLUMNS:
            if self.columns_visible.get(col['id'], True):
                header_label = Label(
                    text=col['label'],
                    size_hint_x=None,
                    width=dp(col['width']),
                    bold=True,
                    color=(0.2, 0.6, 1, 1),
                    font_size=sp(16),
                    halign='left',
                    valign='middle',
                    text_size=(dp(col['width'] - 10), None)
                )
                header_label.bind(size=header_label.setter('text_size'))
                header.add_widget(header_label)
        
        self.data_container.add_widget(header)
    
    def update_data(self, data_rows):
        """Update table with new data"""
        # Clear existing rows (keep header)
        children = list(self.data_container.children)
        for child in children[:-1]:  # Keep last child (header)
            self.data_container.remove_widget(child)
        
        # Add new rows
        for row_data in reversed(data_rows):  # Reverse to maintain order
            row = DataRow(row_data, self.columns_visible)
            self.data_container.add_widget(row)
    
    def update_columns_visibility(self, columns_visible):
        """Update which columns are visible"""
        self.columns_visible = columns_visible
        
        # Recreate header
        self.data_container.clear_widgets()
        self.create_header()


class StatusIndicator(BoxLayout):
    """Status indicator widget for system components"""
    
    status = StringProperty('Unknown')
    color = ListProperty([0.5, 0.5, 0.5, 1])
    
    def __init__(self, label_text, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(30)
        self.spacing = dp(10)
        
        self.label = Label(
            text=label_text,
            size_hint_x=0.7,
            font_size=sp(14),
            halign='left',
            valign='middle'
        )
        self.label.bind(size=self.label.setter('text_size'))
        
        self.status_label = Label(
            text=self.status,
            size_hint_x=0.3,
            font_size=sp(14),
            color=self.color,
            halign='right',
            valign='middle'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        
        self.add_widget(self.label)
        self.add_widget(self.status_label)
    
    def update_status(self, status, color):
        """Update the status display"""
        self.status = status
        self.color = color
        self.status_label.text = status
        self.status_label.color = color


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class MedicalInventoryApp(App):
    """Main Kivy application for Medical Inventory System"""
    
    def build(self):
        """Build the application UI"""
        Window.clearcolor = (0.1, 0.1, 0.1, 1)
        
        # Initialize core components
        self.db = DatabaseManager(DB_FILE)
        self._all_rows = []
        self.fr_ready = False
        self.camera_ready = False
        
        # Start background tasks
        threading.Thread(target=self._preload_facial_recognition, daemon=True).start()
        threading.Thread(target=self._camera_recovery_monitor, daemon=True).start()
        
        # Create main layout
        root = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Title
        title = Label(
            text='Medical Inventory System',
            size_hint_y=None,
            height=dp(60),
            font_size=sp(28),
            bold=True,
            color=(0.2, 0.6, 1, 1)
        )
        root.add_widget(title)
        
        # Main content area (horizontal split)
        content = BoxLayout(orientation='horizontal', spacing=dp(10))
        
        # Left sidebar
        sidebar = self.create_sidebar()
        content.add_widget(sidebar)
        
        # Right content (data table)
        self.data_table = DataTable(size_hint_x=0.7)
        content.add_widget(self.data_table)
        
        root.add_widget(content)
        
        # Status bar
        status_bar = self.create_status_bar()
        root.add_widget(status_bar)
        
        # Load initial data
        Clock.schedule_once(lambda dt: self.load_data(), 0.5)
        Clock.schedule_interval(lambda dt: self.refresh_data(), REFRESH_INTERVAL)
        
        # Keyboard shortcuts
        Window.bind(on_key_down=self._on_keyboard_down)
        
        return root
    
    def create_sidebar(self):
        """Create the left sidebar with controls"""
        sidebar = BoxLayout(
            orientation='vertical',
            size_hint_x=0.3,
            spacing=dp(10),
            padding=dp(10)
        )
        
        # Search section
        search_label = Label(
            text='Search',
            size_hint_y=None,
            height=dp(30),
            font_size=sp(18),
            bold=True,
            halign='left',
            valign='middle'
        )
        search_label.bind(size=search_label.setter('text_size'))
        sidebar.add_widget(search_label)
        
        self.search_input = TextInput(
            size_hint_y=None,
            height=dp(40),
            font_size=sp(16),
            multiline=False,
            hint_text='Search all fields...'
        )
        self.search_input.bind(text=lambda instance, value: self.apply_filters())
        sidebar.add_widget(self.search_input)
        
        # Filter section
        filter_label = Label(
            text='Filters',
            size_hint_y=None,
            height=dp(30),
            font_size=sp(18),
            bold=True,
            halign='left',
            valign='middle'
        )
        filter_label.bind(size=filter_label.setter('text_size'))
        sidebar.add_widget(filter_label)
        
        self.filter_spinner = Spinner(
            text='All',
            values=('All', 'Expiring Soon', 'Expired'),
            size_hint_y=None,
            height=dp(40),
            font_size=sp(16)
        )
        self.filter_spinner.bind(text=lambda instance, value: self.apply_filters())
        sidebar.add_widget(self.filter_spinner)
        
        self.low_stock_checkbox = CheckBox(
            size_hint_y=None,
            height=dp(30),
            active=False
        )
        self.low_stock_checkbox.bind(active=lambda instance, value: self.apply_filters())
        
        low_stock_box = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30)
        )
        low_stock_box.add_widget(self.low_stock_checkbox)
        low_stock_box.add_widget(Label(
            text='Show low stock only',
            font_size=sp(14),
            halign='left',
            valign='middle'
        ))
        sidebar.add_widget(low_stock_box)
        
        # Column visibility section
        col_label = Label(
            text='Show Columns',
            size_hint_y=None,
            height=dp(30),
            font_size=sp(18),
            bold=True,
            halign='left',
            valign='middle'
        )
        col_label.bind(size=col_label.setter('text_size'))
        sidebar.add_widget(col_label)
        
        # Scrollable column checkboxes
        col_scroll = ScrollView(size_hint_y=None, height=dp(200))
        col_container = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        col_container.bind(minimum_height=col_container.setter('height'))
        
        self.column_checkboxes = {}
        for col in COLUMNS:
            box = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(30)
            )
            cb = CheckBox(active=True, size_hint_x=0.2)
            cb.bind(active=lambda instance, value, c=col['id']: self.update_column_visibility(c, value))
            self.column_checkboxes[col['id']] = cb
            
            box.add_widget(cb)
            box.add_widget(Label(
                text=col['label'],
                font_size=sp(14),
                halign='left',
                valign='middle',
                size_hint_x=0.8
            ))
            col_container.add_widget(box)
        
        col_scroll.add_widget(col_container)
        sidebar.add_widget(col_scroll)
        
        # Spacer
        sidebar.add_widget(Label(size_hint_y=1))
        
        # Action buttons
        self.scan_btn = Button(
            text='Scan Barcode',
            size_hint_y=None,
            height=dp(50),
            font_size=sp(16),
            background_color=(0.2, 0.6, 1, 1)
        )
        self.scan_btn.bind(on_press=self.scan_barcode)
        sidebar.add_widget(self.scan_btn)
        
        self.face_scan_btn = Button(
            text='Face Recognition',
            size_hint_y=None,
            height=dp(50),
            font_size=sp(16),
            background_color=(0.2, 0.6, 1, 1)
        )
        self.face_scan_btn.bind(on_press=self.start_face_recognition)
        sidebar.add_widget(self.face_scan_btn)
        
        self.add_drug_btn = Button(
            text='Add New Drug',
            size_hint_y=None,
            height=dp(50),
            font_size=sp(16),
            background_color=(0.2, 0.8, 0.2, 1)
        )
        self.add_drug_btn.bind(on_press=self.add_new_drug)
        sidebar.add_widget(self.add_drug_btn)
        
        self.history_btn = Button(
            text='View History',
            size_hint_y=None,
            height=dp(50),
            font_size=sp(16),
            background_color=(0.8, 0.6, 0.2, 1)
        )
        self.history_btn.bind(on_press=self.view_history)
        sidebar.add_widget(self.history_btn)
        
        return sidebar
    
    def create_status_bar(self):
        """Create status bar at the bottom"""
        status_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            padding=dp(10),
            spacing=dp(20)
        )
        
        self.camera_status = StatusIndicator('Camera:', status='Checking...', color=[1, 1, 0, 1])
        self.fr_status = StatusIndicator('Face Recognition:', status='Loading...', color=[1, 1, 0, 1])
        self.db_status = StatusIndicator('Database:', status='Connected', color=[0, 1, 0, 1])
        
        status_bar.add_widget(self.camera_status)
        status_bar.add_widget(self.fr_status)
        status_bar.add_widget(self.db_status)
        
        return status_bar
    
    # ========================================================================
    # DATA MANAGEMENT
    # ========================================================================
    
    def load_data(self):
        """Load inventory data from database"""
        try:
            rows = self.db.get_inventory()
            self._all_rows = []
            
            for row in rows:
                self._all_rows.append({
                    'drug': row[0],
                    'barcode': row[1],
                    'est_amount': str(row[2]),
                    'exp_date': row[3],
                    'type_': row[4],
                    'dose_size': row[5],
                    'item_type': row[6],
                    'item_loc': row[7] if len(row) > 7 else 'N/A'
                })
            
            self.apply_filters()
            self.update_db_status('Connected', [0, 1, 0, 1])
        except Exception as e:
            print(f"Error loading data: {e}")
            self.update_db_status('Error', [1, 0, 0, 1])
    
    def refresh_data(self):
        """Refresh data periodically"""
        self.load_data()
    
    def apply_filters(self):
        """Apply search and filter criteria"""
        search_text = self.search_input.text.lower()
        filter_type = self.filter_spinner.text
        low_stock_only = self.low_stock_checkbox.active
        
        filtered_rows = []
        
        for row in self._all_rows:
            # Apply search filter
            if search_text:
                row_text = ' '.join([str(v) for v in row.values()]).lower()
                if search_text not in row_text:
                    continue
            
            # Apply expiration filter
            if filter_type == 'Expiring Soon':
                try:
                    exp_date = datetime.strptime(row['exp_date'], '%Y-%m-%d')
                    if exp_date > datetime.now() + timedelta(days=30):
                        continue
                except:
                    continue
            elif filter_type == 'Expired':
                try:
                    exp_date = datetime.strptime(row['exp_date'], '%Y-%m-%d')
                    if exp_date >= datetime.now():
                        continue
                except:
                    continue
            
            # Apply low stock filter
            if low_stock_only:
                try:
                    if int(row['est_amount']) >= 10:
                        continue
                except:
                    continue
            
            filtered_rows.append(row)
        
        self.data_table.update_data(filtered_rows)
    
    def update_column_visibility(self, column_id, visible):
        """Update column visibility"""
        columns_visible = {col['id']: self.column_checkboxes[col['id']].active for col in COLUMNS}
        self.data_table.update_columns_visibility(columns_visible)
        self.apply_filters()
    
    # ========================================================================
    # STATUS UPDATES
    # ========================================================================
    
    @mainthread
    def update_camera_status(self, status, color):
        """Update camera status indicator"""
        self.camera_status.update_status(status, color)
    
    @mainthread
    def update_fr_status(self, status, color):
        """Update face recognition status indicator"""
        self.fr_status.update_status(status, color)
    
    @mainthread
    def update_db_status(self, status, color):
        """Update database status indicator"""
        self.db_status.update_status(status, color)
    
    # ========================================================================
    # BACKGROUND TASKS
    # ========================================================================
    
    def _preload_facial_recognition(self):
        """Preload facial recognition in background"""
        try:
            fr.preload()
            self.fr_ready = True
            self.update_fr_status('Ready', [0, 1, 0, 1])
        except Exception as e:
            print(f"Face recognition preload failed: {e}")
            self.fr_ready = False
            self.update_fr_status('Error', [1, 0, 0, 1])
    
    def _camera_recovery_monitor(self):
        """Monitor camera status"""
        while True:
            try:
                camera = fr._app_cached_camera
                if camera and camera.isOpened():
                    self.camera_ready = True
                    self.update_camera_status('Ready', [0, 1, 0, 1])
                else:
                    self.camera_ready = False
                    self.update_camera_status('Disconnected', [1, 0, 0, 1])
            except Exception as e:
                self.camera_ready = False
                self.update_camera_status('Error', [1, 0, 0, 1])
            
            time.sleep(5)
    
    # ========================================================================
    # ACTION HANDLERS
    # ========================================================================
    
    def scan_barcode(self, instance):
        """Handle barcode scanning"""
        popup_content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        popup_content.add_widget(Label(
            text='Enter Barcode:',
            size_hint_y=None,
            height=dp(30),
            font_size=sp(16)
        ))
        
        barcode_input = TextInput(
            size_hint_y=None,
            height=dp(40),
            font_size=sp(16),
            multiline=False
        )
        popup_content.add_widget(barcode_input)
        
        action_label = Label(
            text='Action:',
            size_hint_y=None,
            height=dp(30),
            font_size=sp(16)
        )
        popup_content.add_widget(action_label)
        
        action_spinner = Spinner(
            text='Add to Inventory',
            values=('Add to Inventory', 'Remove from Inventory', 'Use Item'),
            size_hint_y=None,
            height=dp(40),
            font_size=sp(16)
        )
        popup_content.add_widget(action_spinner)
        
        user_input = TextInput(
            hint_text='User name',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(16),
            multiline=False
        )
        popup_content.add_widget(user_input)
        
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        popup = Popup(
            title='Scan Barcode',
            content=popup_content,
            size_hint=(0.8, 0.6)
        )
        
        def submit(instance):
            barcode = barcode_input.text.strip()
            user = user_input.text.strip() or 'Unknown'
            action = action_spinner.text
            
            if not barcode:
                self.show_message('Error', 'Please enter a barcode')
                return
            
            try:
                if action == 'Add to Inventory':
                    result = self.db.add_to_inventory(barcode, user)
                elif action == 'Remove from Inventory':
                    result = self.db.remove_from_inventory(barcode, user)
                else:  # Use Item
                    result = self.db.use_drug(barcode, user, 1)
                
                if result is None:
                    self.show_message('Success', f'{action} completed successfully')
                    self.load_data()
                    popup.dismiss()
                else:
                    self.show_message('Error', f'Operation failed: {result}')
            except Exception as e:
                self.show_message('Error', str(e))
        
        submit_btn = Button(text='Submit', font_size=sp(16))
        submit_btn.bind(on_press=submit)
        buttons.add_widget(submit_btn)
        
        cancel_btn = Button(text='Cancel', font_size=sp(16))
        cancel_btn.bind(on_press=popup.dismiss)
        buttons.add_widget(cancel_btn)
        
        popup_content.add_widget(buttons)
        popup.open()
    
    def start_face_recognition(self, instance):
        """Start face recognition"""
        if not self.fr_ready:
            self.show_message('Error', 'Face recognition system not ready')
            return
        
        if not self.camera_ready:
            self.show_message('Error', 'Camera not available')
            return
        
        def recognize_thread():
            try:
                result = fr.recognize_face()
                
                if result == "Unknown":
                    self.show_message('Face Recognition', 'Unknown person detected')
                elif result:
                    self.show_message('Face Recognition', f'Recognized: {result}')
                else:
                    self.show_message('Error', 'No face detected')
            except Exception as e:
                self.show_message('Error', f'Face recognition failed: {e}')
        
        threading.Thread(target=recognize_thread, daemon=True).start()
    
    def add_new_drug(self, instance):
        """Show dialog to add new drug"""
        popup_content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        fields = [
            ('Barcode:', 'barcode'),
            ('Drug Name:', 'name'),
            ('Amount:', 'amount'),
            ('Expiration (YYYY-MM-DD):', 'expiration'),
            ('Type:', 'type'),
            ('Dose Size:', 'dose'),
            ('Item Type:', 'item_type')
        ]
        
        inputs = {}
        for label, key in fields:
            popup_content.add_widget(Label(
                text=label,
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                halign='left',
                valign='middle'
            ))
            
            text_input = TextInput(
                size_hint_y=None,
                height=dp(35),
                font_size=sp(14),
                multiline=False
            )
            inputs[key] = text_input
            popup_content.add_widget(text_input)
        
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        popup = Popup(
            title='Add New Drug',
            content=popup_content,
            size_hint=(0.8, 0.8)
        )
        
        def submit(instance):
            try:
                barcode = inputs['barcode'].text.strip()
                name = inputs['name'].text.strip()
                amount = int(inputs['amount'].text.strip())
                expiration = inputs['expiration'].text.strip()
                drug_type = inputs['type'].text.strip()
                dose = inputs['dose'].text.strip()
                item_type = inputs['item_type'].text.strip()
                
                if not all([barcode, name, expiration, drug_type, dose, item_type]):
                    self.show_message('Error', 'All fields are required')
                    return
                
                self.db.add_drug(barcode, name, amount, expiration, drug_type, item_type, dose)
                self.show_message('Success', 'Drug added successfully')
                self.load_data()
                popup.dismiss()
            except Exception as e:
                self.show_message('Error', f'Failed to add drug: {e}')
        
        submit_btn = Button(text='Add Drug', font_size=sp(16))
        submit_btn.bind(on_press=submit)
        buttons.add_widget(submit_btn)
        
        cancel_btn = Button(text='Cancel', font_size=sp(16))
        cancel_btn.bind(on_press=popup.dismiss)
        buttons.add_widget(cancel_btn)
        
        popup_content.add_widget(buttons)
        popup.open()
    
    def view_history(self, instance):
        """View transaction history"""
        try:
            history = self.db.get_drug_changes()
            
            popup_content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
            
            scroll = ScrollView()
            history_container = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
            history_container.bind(minimum_height=history_container.setter('height'))
            
            for entry in history[-50:]:  # Last 50 entries
                text = f"{entry[5]} - {entry[1]} ({entry[0]}): {entry[2]:+d} by {entry[3]}"
                if entry[6]:
                    text += f" - {entry[6]}"
                
                history_label = Label(
                    text=text,
                    size_hint_y=None,
                    height=dp(30),
                    font_size=sp(12),
                    halign='left',
                    valign='middle',
                    color=(1, 1, 1, 1)
                )
                history_label.bind(size=history_label.setter('text_size'))
                history_container.add_widget(history_label)
            
            scroll.add_widget(history_container)
            popup_content.add_widget(scroll)
            
            close_btn = Button(
                text='Close',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(16)
            )
            popup_content.add_widget(close_btn)
            
            popup = Popup(
                title='Transaction History',
                content=popup_content,
                size_hint=(0.9, 0.9)
            )
            
            close_btn.bind(on_press=popup.dismiss)
            popup.open()
        except Exception as e:
            self.show_message('Error', f'Failed to load history: {e}')
    
    def show_message(self, title, message):
        """Show a simple message popup"""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=message, font_size=sp(16)))
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.6, 0.4)
        )
        
        close_btn = Button(
            text='OK',
            size_hint_y=None,
            height=dp(50),
            font_size=sp(16)
        )
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        
        popup.open()
    
    def _on_keyboard_down(self, window, key, *args):
        """Handle keyboard shortcuts"""
        # F11 for fullscreen toggle
        if key == 292:  # F11
            Window.fullscreen = 'auto' if not Window.fullscreen else False
        # Escape to exit fullscreen
        elif key == 27:  # Escape
            if Window.fullscreen:
                Window.fullscreen = False
        
        return True


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    MedicalInventoryApp().run()
