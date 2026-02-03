"""
Medical Inventory System - Main Application
NASA HUNCH Project 2025-26

This application manages medical inventory with barcode scanning,
facial recognition, and usage tracking.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import os
import sys
import datetime
import tkcalendar as tkcal
import threading
import time
import tkinter.font as tkfont

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import facial_recognition as fr
from Database.database import DatabaseManager
from facial_recognition import FaceRecognitionError

# ============================================================================
# CONSTANTS
# ============================================================================

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Database/inventory.db")
REFRESH_INTERVAL = 30000  # milliseconds

# UI Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# ============================================================================
# COLUMN CONFIGURATION
# ============================================================================
#region Column Configurations
COLUMN_CONFIGS = {
    "drug": {"text": "Drug", "width": 220},
    "barcode": {"text": "Barcode", "width": 170},
    "est_amount": {"text": "Amt~", "width": 100},
    "exp_date": {"text": "Expiration", "width": 140},
    "type_": {"text": "Type", "width": 120},
    "dose_size": {"text": "Dose Size", "width": 140},
    "item_type": {"text": "Item Type", "width": 140},
    "item_loc": {"text": "Location", "width": 100}
}

COLUMN_LABELS = {
    "drug": "Drug",
    "barcode": "Barcode",
    "est_amount": "Amt~",
    "exp_date": "Expiration",
    "type_": "Type",
    "dose_size": "Dose Size",
    "item_type": "Item Type",
    "item_loc": "Location"
}
#endregion

# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================
#region Main Application Class
class BarcodeViewer(ctk.CTk):
    """Main application window for Medical Inventory System"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.db = DatabaseManager(DB_FILE)
        self._all_rows = []
        self.fr_ready = False
        self.camera_ready = False
        
        # Start background tasks
        self._start_preloading()
        self._start_camera_recovery_monitor()
        
        # Setup UI
        self._setup_window()
        self._setup_styles()
        self._setup_ui()
        
        # Load initial data
        self.load_data()
        self.after(500, lambda: self._adjust_column_widths([c for c, v in self.column_visibility.items() if v.get()]))
        self.after(REFRESH_INTERVAL, self.refresh_data)
    #endregion

    # ========================================================================
    # WINDOW SETUP
    # ========================================================================
    #region window setup
    def _setup_window(self):
        """Configure main window properties"""
        self.title("Medical Inventory System")
        
        try:
            self.attributes("-fullscreen", True)
        except Exception:
            try:
                self.state("zoomed")
            except Exception:
                self.geometry("1200x800")
        
        # Keyboard shortcuts
        self.bind("<F11>", lambda e: self.attributes("-fullscreen", not self.attributes("-fullscreen")))
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
    
    def _setup_styles(self):
        """Configure ttk styles for consistent appearance"""
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 28))
        style.configure("TButton", font=("Arial", 24), padding=20)
        style.configure("Treeview", font=("Arial", 22), rowheight=55)
        style.configure("Treeview.Heading", font=("Arial", 24, "bold"))
        
        # Configure scrollbar thickness
        style.configure("Vertical.TScrollbar", width=30)  # Make vertical scrollbar 30 pixels wide
        style.configure("Horizontal.TScrollbar", width=30)  # Make horizontal scrollbar 30 pixels tall
        
        # Optional: Customize scrollbar colors for better visibility
        style.map("Vertical.TScrollbar",
            background=[("active", "#5F84C8"), ("!active", "#4a4a4a")],
            troughcolor=[("", "#2b2b2b")]
        )
        style.map("Horizontal.TScrollbar",
            background=[("active", "#5F84C8"), ("!active", "#4a4a4a")],
            troughcolor=[("", "#2b2b2b")]
        )
    #endregion

    # ========================================================================
    # UI CONSTRUCTION
    # ========================================================================
    #region ui construction
    def _setup_ui(self):
        """Build the complete user interface with grid layout"""
        # Configure root window grid
        self.grid_rowconfigure(0, weight=0)  # Title - fixed height
        self.grid_rowconfigure(1, weight=1)  # Main content - flexible
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        ctk.CTkLabel(self, text="Medical Inventory System", font=("Arial", 40, "bold")).grid(
            row=0, column=0, sticky="ew", pady=25
        )
        
        # Main container
        main_frame = ctk.CTkFrame(self, corner_radius=0)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=18, pady=(10, 25))
        
        # Configure main frame grid (2 columns: sidebar + content)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=0, minsize=420)  # Sidebar - fixed width
        main_frame.grid_columnconfigure(1, weight=1)  # Content - flexible
        
        # Sidebar and content areas
        self._create_sidebar(main_frame)
        self._create_content_area(main_frame)

    def _create_content_area(self, parent):
        """Create main content area with data table using grid"""
        content_frame = ctk.CTkFrame(parent, corner_radius=6)
        content_frame.grid(row=0, column=1, sticky="nsew", padx=(12, 18), pady=18)
        
        # Configure content frame
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview
        columns = ("drug", "barcode", "est_amount", "exp_date", "type_", "dose_size", "item_type", "item_loc")
        self.tree = ttk.Treeview(content_frame, columns=columns, show="headings", selectmode="extended")
        
        # Configure columns
        for col_id, config in self.column_configs.items():
            self.tree.heading(col_id, text=config["text"])
            self.tree.column(col_id, width=config["width"])
        
        # Bind events
        self.tree.bind("<Configure>", self._on_tree_configure)
        self.tree.bind("<Button-1>", self._on_tree_click)
        
        # Scrollbar
        scroll = ttk.Scrollbar(content_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        # Grid widgets
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(18, 0), pady=(18, 25))
        scroll.grid(row=0, column=1, sticky="ns", padx=(0, 18), pady=(18, 25))
    
    def _create_sidebar(self, parent):
        """Create left sidebar with controls using grid (flexbox-like)"""
        sidebar = ctk.CTkFrame(parent, width=420, corner_radius=8)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(18, 12), pady=18)
        
        # Configure sidebar to expand vertically - adjusted weights
        sidebar.grid_rowconfigure(0, weight=0)  # Search section - fixed
        sidebar.grid_rowconfigure(1, weight=0)  # Filter section - fixed
        sidebar.grid_rowconfigure(2, weight=3)  # Column visibility - flexible (increased weight)
        sidebar.grid_rowconfigure(3, weight=0)  # Removed spacer row
        sidebar.grid_rowconfigure(4, weight=0)  # Action buttons - fixed
        sidebar.grid_columnconfigure(0, weight=1)
        
        # Search section
        self._create_search_section_grid(sidebar, row=0)
        
        # Filter section
        self._create_filter_section_grid(sidebar, row=1)
        
        # Column visibility section
        self._create_column_visibility_section_grid(sidebar, row=2)
        
        # Action buttons (stays at bottom)
        self._create_action_buttons_grid(sidebar, row=4)

    def _create_search_section_grid(self, parent, row):
        """Create search input section with grid"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", padx=25, pady=(25, 10))
        
        ctk.CTkLabel(frame, text="Search", anchor="w", font=("Arial", 22)).pack(fill="x", pady=(0, 10))
        
        # Entry with button frame
        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x")
        
        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            entry_frame,
            textvariable=self.search_var,
            placeholder_text="Search all fields...",
            height=50,
            font=("Arial", 20)
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        search_entry.bind("<KeyRelease>", self.apply_search_filter)
        
        # Keyboard button
        ctk.CTkButton(
            entry_frame,
            text="⌨",
            command=lambda: self._show_search_keyboard(),
            width=60,
            height=50,
            font=("Arial", 24)
        ).pack(side="left")

    def _show_search_keyboard(self):
        """Show virtual keyboard for search"""
        current_text = self.search_var.get()
        result = VirtualKeyboard.get_input(
            self,
            title="Search Keyboard",
            prompt="Enter search terms:",
            initial_text=current_text
        )
        if result is not None:
            self.search_var.set(result)
            self.apply_search_filter()

    def _create_filter_section_grid(self, parent, row):
        """Create filter controls with grid"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", padx=25, pady=10)
        
        ctk.CTkLabel(frame, text="Filters", anchor="w", font=("Arial", 22)).pack(fill="x", pady=(0, 10))
        
        # Filter dropdown
        self.filter_var = tk.StringVar(value="All")
        filter_opts = ["All", "Expiring Soon", "Expired"]
        ctk.CTkOptionMenu(
            frame,
            values=filter_opts,
            variable=self.filter_var,
            height=50,
            font=("Arial", 20),
            command=lambda v: self.apply_search_filter()
        ).pack(fill="x", pady=(0, 10))
        
        # Low stock checkbox
        self.low_stock_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            frame,
            text="Show low stock only",
            variable=self.low_stock_var,
            font=("Arial", 20),
            command=self.apply_search_filter
        ).pack(fill="x")

    def _create_column_visibility_section_grid(self, parent, row):
        """Create column visibility controls with grid"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="nsew", padx=25, pady=15)
        
        # Configure frame to expand vertically
        frame.grid_rowconfigure(0, weight=0)  # Label - fixed
        frame.grid_rowconfigure(1, weight=1)  # Scrollable frame - flexible
        frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(frame, text="Show Columns", anchor="w", font=("Arial", 22)).grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )
        
        # Initialize column visibility tracking
        columns = ("drug", "barcode", "est_amount", "exp_date", "type_", "dose_size", "item_type", "item_loc")
        self.column_visibility = {col: tk.BooleanVar(value=True) for col in columns}
        self.column_configs = COLUMN_CONFIGS
        
        # Create checkboxes in scrollable frame that expands to fill available space
        columns_frame = ctk.CTkScrollableFrame(frame, corner_radius=6)
        columns_frame.grid(row=1, column=0, sticky="nsew")
        
        for col_id, label in COLUMN_LABELS.items():
            ctk.CTkCheckBox(
                columns_frame,
                text=label,
                variable=self.column_visibility[col_id],
                font=("Arial", 18),
                command=self.update_column_visibility
            ).pack(padx=12, pady=5, anchor="w")

    def _create_button_with_indicator(self, parent, text, command, btn_name, indicator_name):
        """Create a button with status indicator"""
        # Create button
        btn = ctk.CTkButton(
            parent,
            text=text,
            state="enabled",
            command=command,
            height=60,
            font=("Arial", 22)
        )
        btn.pack(fill="x", pady=6, padx=12)
        setattr(self, btn_name, btn)
        
        # Create status indicator
        indicator = ctk.CTkFrame(
            parent,
            width=18,
            height=18,
            corner_radius=12,
            fg_color="#94a3b8",
            bg_color="#1f538d"
        )
        indicator.pack_propagate(False)
        indicator.place(in_=btn, relx=1.0, rely=0.5, anchor="e", x=-12)
        setattr(self, indicator_name, indicator)
        
        # Hover effects
        def on_enter(_):
            indicator.configure(bg_color="#14375e")
        
        def on_leave(_):
            indicator.configure(bg_color="#1f538d")
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        indicator.tkraise()

    def _create_action_buttons_grid(self, parent, row):
        """Create action button section with grid"""
        btns_frame = ctk.CTkFrame(parent, corner_radius=6)
        btns_frame.grid(row=row, column=0, sticky="ew", padx=25, pady=(10, 25))
        
        # Configure button frame
        btns_frame.grid_columnconfigure(0, weight=1)
        
        current_row = 0
        
        # Log Item Use button with indicator
        btn_frame = ctk.CTkFrame(btns_frame, fg_color="transparent")
        btn_frame.grid(row=current_row, column=0, sticky="ew", pady=6, padx=6)
        self._create_button_with_indicator(
            btn_frame,
            "Log Item Use",
            self.log_item_use,
            "log_scan_btn",
            "log_scan_indicator"
        )
        current_row += 1
        
        # Personal Database button with indicator
        btn_frame2 = ctk.CTkFrame(btns_frame, fg_color="transparent")
        btn_frame2.grid(row=current_row, column=0, sticky="ew", pady=6, padx=6)
        self._create_button_with_indicator(
            btn_frame2,
            "View Personal Database",
            lambda: self.personal_run(),
            "personal_db_btn",
            "personal_db_indicator"
        )
        current_row += 1
        
        # Other action buttons
        ctk.CTkButton(
            btns_frame,
            text="Delete Selected",
            command=self.delete_selected,
            height=60,
            font=("Arial", 22)
        ).grid(row=current_row, column=0, sticky="ew", pady=6, padx=12)
        current_row += 1
        
        ctk.CTkButton(
            btns_frame,
            text="View History",
            command=self.show_history,
            height=60,
            font=("Arial", 22)
        ).grid(row=current_row, column=0, sticky="ew", pady=6, padx=12)
        current_row += 1
        
        ctk.CTkButton(
            btns_frame,
            text="Quit",
            command=self.destroy,
            height=60,
            font=("Arial", 22),
            fg_color="#b22222"
        ).grid(row=current_row, column=0, sticky="ew", pady=6, padx=12)
    #endregion

    # ========================================================================
    # FACIAL RECOGNITION
    # ========================================================================
    #region facial recognition
    def _start_preloading(self):
        """Start preloading facial recognition in background"""
        def preload_worker():
            try:
                result = fr.preload_everything()
                
                if result == FaceRecognitionError.SUCCESS:
                    self.fr_ready = fr.preloading_complete
                    self.camera_ready = fr.camera_ready
                    
                    if self.fr_ready:
                        self.after(0, self._enable_facial_recognition_ui)
                    else:
                        self.after(0, self._disable_facial_recognition_ui)
                else:
                    self.fr_ready = False
                    self.camera_ready = False
                    self.after(500, lambda: self._show_fr_error(result))
            except Exception as e:
                print(f"Preloading error: {e}")
                error_msg = f"Failed to initialize facial recognition system:\n{str(e)}"
                self.after(500, lambda: self.show_popup("Initialization Error", error_msg, "error"))
        
        thread = threading.Thread(target=preload_worker, daemon=True)
        thread.start()
    
    def _enable_facial_recognition_ui(self):
        """Enable UI elements that require facial recognition"""
        try:
            if hasattr(self, 'log_scan_btn'):
                self.log_scan_btn.configure(text="Log Item Use", state="normal")
            if hasattr(self, 'personal_db_btn'):
                self.personal_db_btn.configure(text="View Personal Database", state="normal")
            self.set_status_indicator("#22c55e", "log_scan_indicator")
            self.set_status_indicator("#22c55e", "personal_db_indicator")
        except Exception as e:
            print(f"Error enabling UI: {e}")
    
    def _disable_facial_recognition_ui(self):
        """Disable UI elements that require facial recognition"""
        try:
            if hasattr(self, 'log_scan_btn'):
                self.log_scan_btn.configure(text="Log Item Use", state="disabled")
            if hasattr(self, 'personal_db_btn'):
                self.personal_db_btn.configure(text="View Personal Database", state="disabled")
            self.set_status_indicator("#94a3b8", "log_scan_indicator")
            self.set_status_indicator("#94a3b8", "personal_db_indicator")
        except Exception as e:
            print(f"Error disabling UI: {e}")
    
    def _show_fr_error(self, result):
        """Show facial recognition initialization error"""
        error_messages = {
            FaceRecognitionError.REFERENCE_FOLDER_ERROR: "Reference folder not found. Please add reference images to assets/references/",
            FaceRecognitionError.MODEL_LOAD_FAILED: "Failed to load face recognition model. Please check dependencies.",
            FaceRecognitionError.PRELOAD_FAILED: "Failed to initialize facial recognition system.",
            FaceRecognitionError.CAMERA_ERROR: "Camera not found or could not be initialized.",
        }
        
        error_msg = error_messages.get(result, f"Initialization failed: {result.message}")
        
        try:
            self.show_popup("Initialization Error", error_msg, "error")
            self.log_scan_btn.configure(text="Log Item Use", state="disabled")
        except Exception as ui_error:
            print(f"Failed to show error dialog: {ui_error}")
    
    def _start_camera_recovery_monitor(self):
        """Monitor camera status and attempt recovery if disconnected"""
        def camera_monitor():
            check_interval = 5
            max_interval = 120
            
            while True:
                try:
                    if not self.camera_ready and self.fr_ready:
                        if fr.reinitialize_camera():
                            self.camera_ready = True
                            fr.camera_ready = True
                            check_interval = 5
                            self.after(0, self._on_camera_recovered)
                        else:
                            check_interval = min(check_interval * 1.5, max_interval)
                    else:
                        check_interval = 5
                    
                    time.sleep(check_interval)
                except Exception as e:
                    print(f"Camera monitor error: {e}")
                    check_interval = min(check_interval * 2, max_interval)
                    time.sleep(check_interval)
        
        monitor_thread = threading.Thread(target=camera_monitor, daemon=True)
        monitor_thread.start()
    
    def _on_camera_recovered(self):
        """Handle camera recovery"""
        try:
            if hasattr(self, 'log_scan_btn'):
                self.log_scan_btn.configure(state="normal")
            if hasattr(self, 'personal_db_btn'):
                self.personal_db_btn.configure(state="normal")
            self.set_status_indicator("#22c55e", "log_scan_indicator")
            self.set_status_indicator("#22c55e", "personal_db_indicator")
            print("Camera recovered successfully!")
        except Exception as e:
            print(f"Error updating UI after camera recovery: {e}")
    
    def set_status_indicator(self, color, indicator_name="log_scan_indicator"):
        """Update status indicator color"""
        try:
            if hasattr(self, indicator_name):
                getattr(self, indicator_name).configure(fg_color=color)
                getattr(self, indicator_name).update()
        except Exception:
            pass
    
    def face_recognition_with_timeout(self, btn, btn_text):
        """Run face recognition with timeout and visual feedback"""
        indicator_name = "log_scan_indicator" if btn == "log_scan_btn" else "personal_db_indicator"
        
        # Set scanning status
        self.set_status_indicator("#f59e0b", indicator_name)
        if hasattr(self, btn):
            getattr(self, btn).configure(state="disabled", text="Scanning...")
        
        result = {"value": None, "completed": False}
        
        def recognition_worker():
            try:
                if self.fr_ready:
                    result["value"] = fr.quick_detect()
                else:
                    result["value"] = fr.main()
                result["completed"] = True
            except Exception as e:
                result["value"] = f"Error: {e}"
                result["completed"] = True
        
        thread = threading.Thread(target=recognition_worker, daemon=True)
        thread.start()
        
        # Wait with timeout
        timeout_seconds = 5
        start_time = time.time()
        
        while not result["completed"] and (time.time() - start_time) < timeout_seconds:
            self.update()
            time.sleep(0.1)
        
        # Reset button
        if hasattr(self, btn):
            getattr(self, btn).configure(state="normal", text=btn_text)
        
        if not result["completed"]:
            self.set_status_indicator("#dc2626", indicator_name)
            default_status = "#22c55e" if self.fr_ready else "#94a3b8"
            self.after(2000, lambda: self.set_status_indicator(default_status, indicator_name))
            return "timeout"
        else:
            default_status = "#22c55e" if self.fr_ready else "#94a3b8"
            self.set_status_indicator(default_status, indicator_name)
            return result["value"]
    
    def process_face_recognition_result(self, btn, result=None):
        """Process face recognition result and return username"""
        indicator_name = "log_scan_indicator" if btn == "log_scan_btn" else "personal_db_indicator"
        
        # Handle FaceRecognitionError enum types
        if isinstance(result, FaceRecognitionError):
            if result == FaceRecognitionError.CAMERA_ERROR:
                self.show_popup("Camera Error", "Camera could not be initialized.", "error")
                self.camera_ready = False
                self.set_status_indicator("#dc2626", indicator_name)
                if hasattr(self, btn):
                    getattr(self, btn).configure(state="disabled")
            elif result == FaceRecognitionError.CAMERA_DISCONNECTED:
                self.show_popup("Camera Disconnected", "Camera was disconnected. Please reconnect and try again.", "error")
                self.set_status_indicator("#dc2626", indicator_name)
                self.camera_ready = False
                # Attempt to reinitialize camera
                if fr.reinitialize_camera():
                    self.camera_ready = True
                    self.show_popup("Camera Reconnected", "Camera has been reconnected!", "info")
                    if hasattr(self, btn):
                        getattr(self, btn).configure(state="normal")
                else:
                    if hasattr(self, btn):
                        getattr(self, btn).configure(state="disabled")
            elif result == FaceRecognitionError.REFERENCE_FOLDER_ERROR:
                self.show_popup("Reference Folder Error", "Reference images folder not found. Please add face images to assets/references/", "error")
            elif result == FaceRecognitionError.FRAME_CAPTURE_FAILED:
                self.show_popup("Frame Capture Error", "Failed to capture frame from camera.", "error")
                self.camera_ready = False
            else:
                self.show_popup("Recognition Error", f"An error occurred: {result.message}", "error")
            return ""
        
        # Handle old numeric error codes
        if isinstance(result, int):
            if result == 4:
                self.show_popup("Camera Error", "Couldn't find camera", "error")
            elif result == 3:
                self.show_popup("Reference Folder Error", "No reference folder found", "error")
            elif result == 2:
                self.show_popup("No Faces Found", "No faces found in reference images", "error")
            return ""
        
        # Handle list/tuple of detected names
        if isinstance(result, (list, tuple)):
            if not result:
                self.show_popup("Face Recognition", "No known faces detected.", "info")
                return ""
            detected_name = str(result[0])
            self.show_popup("Face Recognition", f"Detected: {detected_name}", "info")
            return detected_name
        
        self.show_popup("Face Recognition", f"Unexpected result from recognizer: {result}", "error")
        return ""
    
    def scan_face(self, scan_text, btn, btn_text):
        """Perform face recognition with pre-checks and error handling"""
        if not self.fr_ready:
            self.show_popup("Please Wait", "System is still loading. Please wait and try again.", "info")
            return
        
        if not self.camera_ready:
            print("Camera not ready, attempting to reinitialize...")
            if fr.reinitialize_camera():
                self.camera_ready = True
                fr.camera_ready = True
                print("Camera reinitialized successfully")
            else:
                self.show_popup("Camera Error", "Could not find camera. Please make sure camera is connected.", "error")
                return
        
        user_result = self.face_recognition_with_timeout(btn, btn_text)
        
        if user_result == "timeout":
            self.show_popup("Timeout", "Face recognition timed out after 5 seconds. Please try again.", "error")
            print("Face recognition timeout")
            return
        elif isinstance(user_result, str) and user_result.startswith("Error:"):
            self.show_popup("Error", f"Face recognition failed: {user_result}", "error")
            return
        
        user = self.process_face_recognition_result(btn, user_result)
        
        if not user:
            self.show_popup("Authentication Required", f"Face recognition must be successful to {scan_text}.", "error")
            return
        
        return user
    #endregion

    # ========================================================================
    # DATA MANAGEMENT
    # ========================================================================
    #region data management
    def load_data(self):
        """Read from database and load rows into the table"""
        try:
            rows = list(self.db.pull_data("drugs_in_inventory"))
        except Exception as e:
            print("Error reading database:", e)
            rows = []
        
        self._all_rows = rows
        self.apply_search_filter()
    
    def refresh_data(self):
        """Reload data periodically"""
        self.load_data()
        self.after(REFRESH_INTERVAL, self.refresh_data)
    
    def apply_search_filter(self, event=None):
        #dont get rid of event, its needed for the event binding yes i know its not accessed
        """Apply search and filter UI to the cached DB rows"""
        self.tree.delete(*self.tree.get_children())
        
        rows = getattr(self, "_all_rows", None)
        if rows is None:
            try:
                rows = list(self.db.pull_data("drugs_in_inventory"))
            except Exception:
                rows = []
        
        q = (self.search_var.get() or "").strip().lower()
        mode = (self.filter_var.get() or "All")
        low_only = bool(self.low_stock_var.get())
        low_threshold = 20
        now = datetime.date.today()
        
        filtered_rows = []
        
        for row in rows:
            try:
                barcode, drug, est_amount, exp_date_raw, type_, dose_size, item_type, item_loc = row[0], row[1], row[2], row[3], row[4], row[6], row[5], row[7]
            except Exception:
                vals = list(row)
                barcode = vals[0] if len(vals) > 0 else ""
                drug = vals[1] if len(vals) > 1 else ""
                est_amount = vals[2] if len(vals) > 2 else ""
                exp_date_raw = vals[3] if len(vals) > 3 else None
                type_ = vals[4] if len(vals) > 4 else ""
                dose_size = vals[6] if len(vals) > 5 else ""
                item_type = vals[5] if len(vals) > 6 else ""
                item_loc = vals[7] if len(vals) > 7 else ""
            
            # Search filter
            if q:
                searchable_fields = [
                    str(drug).lower(),
                    str(barcode).lower(),
                    str(type_).lower(),
                    str(dose_size).lower(),
                    str(item_type).lower(),
                    str(item_loc).lower()
                ]
                if not any(q in field for field in searchable_fields):
                    continue
            
            # Low stock filter
            if low_only:
                try:
                    amt = float(est_amount)
                except Exception:
                    continue
                if amt > low_threshold:
                    continue
            
            # Expiration filters
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
            
            display_row = (drug, barcode, est_amount, exp_date_raw, type_, dose_size, item_type, item_loc)
            filtered_rows.append(display_row)
        
        # Sort alphabetically by drug name
        filtered_rows.sort(key=lambda x: str(x[0]).lower())
        
        # Insert sorted rows
        for display_row in filtered_rows:
            self.tree.insert("", "end", values=display_row)
    
    def _parse_date(self, d):
        """Parse date from various formats"""
        if not d:
            return None
        if isinstance(d, datetime.date):
            return d
        s = str(d).strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.datetime.strptime(s, fmt).date()
            except Exception:
                continue
        try:
            return datetime.date.fromisoformat(s)
        except Exception:
            return None
    #endregion

    # ========================================================================
    # USER ACTIONS
    # ========================================================================
    #region user actions
    def personal_run(self):
        """Open personal database window"""
        user = self.scan_face(scan_text="access personal database", btn="personal_db_btn", btn_text="View Personal Database")
        if user is None or user == "":
            return
        Personal_db_window(self, user)
    
    def log_item_use(self, title="Log Item Use"):
        """Show dialog to select action type: Restock or Use Item"""
        user = self.scan_face(scan_text="log item use", btn="log_scan_btn", btn_text="Log Item Use")
        if user is None or user == "":
            return
        
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.transient(self)
        dlg.resizable(False, False)
        
        result = {"value": None}
        
        ctk.CTkLabel(dlg, text="Select Action Type", font=("Arial", 24, "bold")).pack(padx=40, pady=(30, 20))
        ctk.CTkLabel(dlg, text="Choose whether to restock an item or log usage:", 
                    font=("Arial", 18), wraplength=400, justify="center").pack(padx=40, pady=(0, 30))
        
        def on_restock():
            result["value"] = "restock"
            dlg.destroy()
        
        def on_use():
            result["value"] = "use"
            dlg.destroy()
        
        def on_cancel():
            try:
                dlg.grab_release()
            except:
                pass
            dlg.destroy()
        
        btn_frame = ctk.CTkFrame(dlg, corner_radius=6)
        btn_frame.pack(pady=(0, 22), padx=18, fill="x")
        
        ctk.CTkButton(btn_frame, text="Restock", command=on_restock, width=160, height=55, 
                     font=("Arial", 20), fg_color="#22c55e").pack(side="left", padx=12, pady=12)
        ctk.CTkButton(btn_frame, text="Use Item", command=on_use, width=160, height=55, 
                     font=("Arial", 20)).pack(side="left", padx=12, pady=12)
        ctk.CTkButton(btn_frame, text="Cancel", command=on_cancel, width=160, height=55, 
                     font=("Arial", 20), fg_color="gray50").pack(side="left", padx=12, pady=12)
        
        dlg.bind("<Escape>", lambda e: on_cancel())
        
        dlg.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width()//2) - (dlg.winfo_reqwidth()//2)
        y = self.winfo_rooty() + (self.winfo_height()//2) - (dlg.winfo_reqheight()//2)
        dlg.geometry(f"+{x}+{y}")
        
        dlg.lift()
        dlg.grab_set()
        dlg.focus_force()
        
        self.wait_window(dlg)
        
        if result["value"] is None:
            return
        
        if result["value"] == "restock":
            self.log_scan(user=user)
        elif result["value"] == "use":
            self.use_item(user=user)
    
    def log_scan(self, user=None):
        """Log item restock"""
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if user is None or user == "":
            return
        
        barcode = self._prompt_for_barcode()
        if barcode is None:
            return
        
        log = self.db.add_to_inventory(barcode, user)
        
        try:
            if not barcode or barcode.strip() == "":
                self.show_popup("Error", "No barcode scanned.", "error")
                return
            if log == LookupError:
                self.show_popup("Error", f"No drug found with barcode: {barcode}", "error")
                return
            elif log == IndexError:
                self.show_popup("Error", f"Drug with barcode {barcode} is already in inventory.", "error")
                return
        except Exception as e:
            self.show_popup("Error", f"Failed to write to database:\n{e}", "error")
            return
        
        self.load_data()
        self.show_popup("Logged", f"Restocked {barcode} at {time} by {user}", "info")
    
    def use_item(self, user=None):
        """Log item usage"""
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        barcode = self._prompt_for_barcode(prompt="Scan item barcode", title="Item Usage - Scan Barcode")
        if barcode is None or barcode.strip() == "":
            return
        
        exists = self.db.check_if_barcode_exists(barcode)
        
        if not exists:
            self.show_popup("Invalid Barcode", f"Barcode {barcode} not found in inventory.", "error")
            return
        else:
            barcode = exists[1]
        
        amount = self._prompt_for_amount(prompt="Enter amount used", title="Item Usage - Amount")
        if amount is None:
            return
        
        try:
            self.db.log_access_to_inventory(barcode=barcode, change=amount, user=user)
            self.show_popup("Item Used", f"Logged usage:\n{amount} of item {barcode}\nat {time} by {user}", "info")
        except Exception as e:
            self.show_popup("Error", f"Failed to log item usage:\n{e}", "error")
            return
        
        self.load_data()
    
    def delete_selected(self, prompt="Enter reason for deletion", title="Delete Scans"):
        """Delete selected items from inventory"""
        if not self.admin("Enter admin code to delete scans"):
            return
        
        sel = self.tree.selection()
        
        if not sel:
            self.show_popup("Delete", "No row selected.", "info")
            return
        
        # Get deletion reason using virtual keyboard
        reason = VirtualKeyboard.get_input(
            self,
            title=title,
            prompt=prompt,
            initial_text=""
        )
        
        if reason is None:
            return
        if not reason.strip():
            self.show_popup("Error", "A deletion reason is required.", "error")
            return
        
        if not self.show_confirm("Confirm Delete", f"Delete {len(sel)} selected row(s)?\nReason: {reason}"):
            return
        
        try:
            for item_id in sel:
                values = self.tree.item(item_id)["values"]
                barcode_value = values[1] if len(values) > 1 else values[0]
                self.db.delete_entry(barcode=barcode_value, reason=reason)
        except Exception as e:
            self.show_popup("Error", f"Failed to delete from database:\n{e}", "error")
            return
        
        self.load_data()
        self.show_popup("Deleted", f"Deleted {len(sel)} row(s).", "info")
    
    def show_history(self):
        """Show deletion history in a new window"""
        if not self.admin("View History"):
            return
        
        history = ctk.CTkToplevel(self)
        history.title("History")
        
        history.update_idletasks()
        
        screen_width = history.winfo_screenwidth()
        screen_height = history.winfo_screenheight()
        
        try:
            history.attributes("-fullscreen", True)
        except Exception:
            history.geometry(f"{screen_width}x{screen_height}+0+0")
        
        try:
            history.transient(self)
            history.lift()
            history.focus_force()
            
            def do_grab():
                try:
                    history.grab_set()
                except Exception as e:
                    print(f"Could not grab focus: {e}")
            history.after(100, do_grab)
        except Exception as e:
            print(f"Could not make history window modal: {e}")
        
        # Top bar with close button
        top_bar = ctk.CTkFrame(history, corner_radius=6)
        top_bar.pack(fill="x", padx=18, pady=(18, 0))
        ctk.CTkButton(top_bar, text="Close", command=history.destroy, width=160, height=55, 
                     font=("Arial", 22)).pack(side="right", padx=18, pady=18)
        history.bind("<Escape>", lambda e: history.destroy())
        
        # Create treeview
        columns = ("barcode", "name_of_item", "amount_changed", "user", "type", "time", "reason")
        tree = ttk.Treeview(history, columns=columns, show="headings")
        
        tree.heading("barcode", text="Barcode")
        tree.heading("name_of_item", text="Name of Item")
        tree.heading("amount_changed", text="Amount Changed")
        tree.heading("type", text="Type of Change")
        tree.heading("time", text="Time of Change")
        tree.heading("reason", text="Reason")
        tree.heading("user", text="User")
        
        scroll = ttk.Scrollbar(history, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        
        tree.pack(side="left", fill="both", expand=True, padx=(18, 0), pady=18)
        scroll.pack(side="right", fill="y", padx=(0, 18), pady=18)
        
        for row in self.db.pull_data("drug_changes"):
            tree.insert("", "end", values=row)
    #endregion

    # ========================================================================
    # DIALOG HELPERS
    # ========================================================================
    #region dialog helpers
    def _prompt_for_barcode(self, prompt="Scan barcode and press Enter", title="Scan Barcode"):
        """Open modal dialog for barcode entry"""
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.transient(self)
        dlg.resizable(False, False)
        
        ctk.CTkLabel(dlg, text=prompt, anchor="w", font=("Arial", 22)).pack(padx=25, pady=(22, 12))
        
        entry_var = tk.StringVar()
        entry = ctk.CTkEntry(dlg, textvariable=entry_var, width=400, height=55, font=("Arial", 20))
        entry.pack(padx=25, pady=(0, 22))
        
        result = {"value": None}
        
        def on_ok(event=None):
            val = entry_var.get().strip()
            if val == "":
                return
            result["value"] = val
            try:
                dlg.grab_release()
            except:
                pass
            dlg.destroy()
        
        def on_cancel(event=None):
            try:
                dlg.grab_release()
            except:
                pass
            dlg.destroy()
        
        # Numpad
        numpad_frame = ctk.CTkFrame(dlg)
        numpad_frame.pack(pady=(0, 18))
        
        buttons = [
            ['7', '8', '9'],
            ['4', '5', '6'],
            ['1', '2', '3'],
            ['C', '0', '<']
        ]
        
        def add_to_entry(value):
            current = entry_var.get()
            entry_var.set(current + str(value))
        
        def clear_entry():
            entry_var.set("")
        
        def backspace():
            entry_var.set(entry_var.get()[:-1])
        
        for i, row in enumerate(buttons):
            for j, btn_text in enumerate(row):
                if btn_text == 'C':
                    btn = ctk.CTkButton(numpad_frame, text=btn_text, width=110, height=110, 
                                       font=("Arial", 26), command=clear_entry)
                elif btn_text == '<':
                    btn = ctk.CTkButton(numpad_frame, text=btn_text, width=110, height=110, 
                                       font=("Arial", 26), command=backspace)
                else:
                    btn = ctk.CTkButton(numpad_frame, text=btn_text, width=110, height=110, 
                                       font=("Arial", 26), command=lambda x=btn_text: add_to_entry(x))
                btn.grid(row=i, column=j, padx=10, pady=10)
        
        # Buttons
        btn_frame = ctk.CTkFrame(dlg, corner_radius=6)
        btn_frame.pack(pady=(0, 22), padx=18, fill="x")
        ctk.CTkButton(btn_frame, text="OK", command=on_ok, width=160, height=55, 
                     font=("Arial", 20)).pack(side="left", padx=12, pady=12)
        ctk.CTkButton(btn_frame, text="Cancel", command=on_cancel, width=160, height=55, 
                     font=("Arial", 20), fg_color="gray30").pack(side="left", padx=12, pady=12)
        
        entry.bind("<Return>", on_ok)
        dlg.bind("<Escape>", on_cancel)
        
        dlg.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width()//2) - (dlg.winfo_reqwidth()//2)
        y = self.winfo_rooty() + (self.winfo_height()//2) - (dlg.winfo_reqheight()//2)
        dlg.geometry(f"+{x}+{y}")
        
        def do_grab():
            try:
                dlg.grab_set()
                entry.focus_set()
            except:
                pass
        dlg.after(50, do_grab)
        
        self.wait_window(dlg)
        return result["value"]
    
    def _prompt_for_amount(self, prompt="Enter amount", title="Enter Amount"):
        """Open modal dialog for amount entry"""
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.transient(self)
        dlg.resizable(False, False)
        
        ctk.CTkLabel(dlg, text=prompt, anchor="w", font=("Arial", 22)).pack(padx=25, pady=(22, 12))
        
        entry_var = tk.StringVar()
        entry = ctk.CTkEntry(dlg, textvariable=entry_var, width=400, height=55, font=("Arial", 20))
        entry.pack(padx=25, pady=(0, 22))
        
        result = {"value": None}
        
        def on_ok(event=None):
            val = entry_var.get().strip()
            if val == "":
                return
            try:
                float(val)
                result["value"] = val
                try:
                    dlg.grab_release()
                except:
                    pass
                dlg.destroy()
            except ValueError:
                self.show_popup("Invalid Amount", "Please enter a valid number.", "error")
        
        def on_cancel(event=None):
            try:
                dlg.grab_release()
            except:
                pass
            dlg.destroy()
        
        # Numpad
        numpad_frame = ctk.CTkFrame(dlg)
        numpad_frame.pack(pady=(0, 18))
        
        buttons = [
            ['7', '8', '9'],
            ['4', '5', '6'],
            ['1', '2', '3'],
            ['C', '0', '.']
        ]
        
        def add_to_entry(value):
            current = entry_var.get()
            if value == '.' and '.' in current:
                return
            entry_var.set(current + str(value))
        
        def clear_entry():
            entry_var.set("")
        
        def backspace():
            entry_var.set(entry_var.get()[:-1])
        
        for i, row in enumerate(buttons):
            for j, btn_text in enumerate(row):
                if btn_text == 'C':
                    btn = ctk.CTkButton(numpad_frame, text=btn_text, width=110, height=110, 
                                       font=("Arial", 26), command=clear_entry)
                else:
                    btn = ctk.CTkButton(numpad_frame, text=btn_text, width=110, height=110, 
                                       font=("Arial", 26), command=lambda x=btn_text: add_to_entry(x))
                btn.grid(row=i, column=j, padx=10, pady=10)
        
        backspace_btn = ctk.CTkButton(numpad_frame, text="<", width=110, height=110, 
                                      font=("Arial", 26), command=backspace)
        backspace_btn.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        btn_frame = ctk.CTkFrame(dlg, corner_radius=6)
        btn_frame.pack(pady=(0, 22), padx=18, fill="x")
        ctk.CTkButton(btn_frame, text="OK", command=on_ok, width=160, height=55, 
                     font=("Arial", 20)).pack(side="left", padx=12, pady=12)
        ctk.CTkButton(btn_frame, text="Cancel", command=on_cancel, width=160, height=55, 
                     font=("Arial", 20), fg_color="gray30").pack(side="left", padx=12, pady=12)
        
        entry.bind("<Return>", on_ok)
        dlg.bind("<Escape>", on_cancel)
        
        dlg.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width()//2) - (dlg.winfo_reqwidth()//2)
        y = self.winfo_rooty() + (self.winfo_height()//2) - (dlg.winfo_reqheight()//2)
        dlg.geometry(f"+{x}+{y}")
        
        def do_grab():
            try:
                dlg.grab_set()
                entry.focus_set()
            except:
                pass
        dlg.after(50, do_grab)
        
        self.wait_window(dlg)
        
        result_val = result["value"]
        if result_val is not None:
            result_val = int(float(result_val)) * -1
        return result_val
    
    def admin(self, title, prompt="Enter admin code"):
        """Admin authentication dialog"""
        code = 1234
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.transient(self)
        dlg.resizable(False, False)
        
        ctk.CTkLabel(dlg, text=prompt, font=("Arial", 22)).pack(padx=25, pady=(22, 12))
        entry_var = tk.StringVar()
        entry = ctk.CTkEntry(dlg, textvariable=entry_var, width=400, height=55, font=("Arial", 20), show="*")
        entry.pack(padx=25, pady=(0, 22))
        
        button_frame = ctk.CTkFrame(dlg)
        button_frame.pack(pady=(0, 22))
        buttons = [
            ['7', '8', '9'],
            ['4', '5', '6'],
            ['1', '2', '3'],
            ['C', '0', '<']
        ]
        
        def add_to_entry(value):
            current = entry_var.get()
            entry_var.set(current + str(value))
        
        def clear_entry():
            entry_var.set("")
        
        def backspace():
            entry_var.set(entry_var.get()[:-1])
        
        for i, row in enumerate(buttons):
            for j, btn_text in enumerate(row):
                if btn_text == 'C':
                    btn = ctk.CTkButton(button_frame, text=btn_text, width=110, height=110, font=("Arial", 26), command=clear_entry)
                elif btn_text == '<':
                    btn = ctk.CTkButton(button_frame, text=btn_text, width=110, height=110, font=("Arial", 26), command=backspace)
                else:
                    btn = ctk.CTkButton(button_frame, text=btn_text, width=110, height=110, font=("Arial", 26), command=lambda x=btn_text: add_to_entry(x))
                btn.grid(row=i, column=j, padx=10, pady=10)
        
        result = {"value": None}
        btn_frame = ctk.CTkFrame(dlg)
        btn_frame.pack(pady=(0, 22), fill="x")
        
        def on_ok(event=None):
            val = entry_var.get().strip()
            if val != "":
                result["value"] = val
                dlg.destroy()
        
        def on_cancel(event=None):
            dlg.destroy()
        
        ctk.CTkButton(btn_frame, text="OK", command=on_ok, width=160, height=55, 
                     font=("Arial", 20)).pack(side="left", padx=12)
        ctk.CTkButton(btn_frame, text="Cancel", command=on_cancel, width=160, height=55, 
                     font=("Arial", 20), fg_color="gray30").pack(side="right", padx=12)
        
        entry.bind("<Return>", on_ok)
        dlg.bind("<Escape>", on_cancel)
        
        dlg.update_idletasks()
        
        x = self.winfo_rootx() + (self.winfo_width()//2) - (dlg.winfo_reqwidth()//2)
        y = self.winfo_rooty() + (self.winfo_height()//2) - (dlg.winfo_reqheight()//2)
        dlg.geometry(f"+{x}+{y}")
        
        dlg.lift()
        dlg.grab_set()
        dlg.focus_force()
        entry.focus_force()
        try:
            entry.select_range(0, "end")
        except Exception:
            pass
        
        self.wait_window(dlg)
        
        entered = result.get("value")
        if entered is None:
            return False
        elif str(entered) != str(code):
            self.show_popup("Admin Access Denied", "Incorrect admin code.", "error")
            return False
        return True
    
    def show_popup(self, title, message, popup_type="info"):
        """Show custom CTk popup dialog"""
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("520x240")
        popup.resizable(False, False)
        
        popup.after(10, lambda: self._setup_popup_content(popup, title, message, popup_type))
        
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 260
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 120
        popup.geometry(f"520x240+{x}+{y}")
        
        popup.transient(self)
        popup.grab_set()
        
        self.wait_window(popup)
    
    def _setup_popup_content(self, popup, title, message, popup_type):
        """Setup popup content after window is ready"""
        if popup_type == "error":
            accent_color = "#dc2626"
        elif popup_type == "warning":
            accent_color = "#f59e0b"
        else:
            accent_color = "#3b82f6"
        
        ctk.CTkLabel(popup, text=title, font=("Arial", 22, "bold"), text_color=accent_color).pack(pady=(30, 18))
        ctk.CTkLabel(popup, text=message, font=("Arial", 18), wraplength=460, justify="center").pack(pady=(0, 25))
        ctk.CTkButton(popup, text="OK", command=popup.destroy, width=140, height=45, 
                     font=("Arial", 18), fg_color=accent_color).pack()
    
    def show_confirm(self, title, message):
        """Show custom CTk confirmation dialog"""
        result = {"value": False}
        
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("520x260")
        popup.resizable(False, False)
        
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 260
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 130
        popup.geometry(f"520x260+{x}+{y}")
        
        popup.transient(self)
        popup.grab_set()
        
        def on_yes():
            result["value"] = True
            popup.destroy()
        
        def on_no():
            result["value"] = False
            popup.destroy()
        
        def setup_content():
            ctk.CTkLabel(popup, text=title, font=("Arial", 22, "bold"), text_color="#3b82f6").pack(pady=(30, 18))
            ctk.CTkLabel(popup, text=message, font=("Arial", 18), wraplength=460, justify="center").pack(pady=(0, 25))
            
            btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
            btn_frame.pack()
            
            ctk.CTkButton(btn_frame, text="Yes", command=on_yes, width=120, height=45, 
                         font=("Arial", 18)).pack(side="left", padx=12)
            ctk.CTkButton(btn_frame, text="No", command=on_no, width=120, height=45, 
                         font=("Arial", 18), fg_color="gray50").pack(side="left", padx=12)
        
        popup.after(10, setup_content)
        popup.bind("<Escape>", lambda e: on_no())
        
        self.wait_window(popup)
        return result["value"]
    
    def show_error(self, title="Error", message="An error occurred."):
        """Display an error window"""
        self.show_popup(title, message, "error")
    #endregion

    # ========================================================================
    # TREEVIEW MANAGEMENT
    # ========================================================================
    #region treeview management
    def update_column_visibility(self):
        """Update which columns are displayed"""
        visible_columns = [col for col, var in self.column_visibility.items() if var.get()]
        
        if visible_columns:
            self.tree.configure(displaycolumns=visible_columns)
            self.after(50, lambda: self._adjust_column_widths(visible_columns))
        else:
            self.column_visibility["drug"].set(True)
            self.tree.configure(displaycolumns=["drug"])
            self.after(50, lambda: self._adjust_column_widths(["drug"]))
    
    def _on_tree_click(self, event):
        """Toggle selection of clicked row"""
        region = self.tree.identify_region(event.x, event.y)
        if region not in ("cell", "tree"):
            return None
        
        row = self.tree.identify_row(event.y)
        if not row:
            try:
                self.tree.selection_remove(self.tree.selection())
            except Exception:
                pass
            return "break"
        
        cur = list(self.tree.selection())
        if row in cur:
            cur.remove(row)
            self.tree.selection_set(tuple(cur))
        else:
            cur.append(row)
            self.tree.selection_set(tuple(cur))
        
        return "break"
    
    def _on_tree_configure(self, event):
        """Handler for tree resize events"""
        try:
            visible = [col for col, var in self.column_visibility.items() if var.get()]
            try:
                if hasattr(self, "_column_adjust_after_id"):
                    self.after_cancel(self._column_adjust_after_id)
            except Exception:
                pass
            if self.tree.winfo_width() > 1:
                self._column_adjust_after_id = self.after(
                    100, lambda: self._adjust_column_widths(visible)
                )
        except Exception:
            pass
    
    def _adjust_column_widths(self, visible_columns):
        """Distribute available tree width across visible columns"""
        try:
            if not visible_columns:
                return
            
            if not self.tree.winfo_exists():
                return
            
            self.tree.update_idletasks()
            total_width = self.tree.winfo_width()
            
            if total_width <= 10:
                try:
                    total_width = self.tree.master.winfo_width()
                except Exception:
                    total_width = sum(self.column_configs[c]["width"] for c in visible_columns) or 600
            
            if total_width < 100:
                return
            
            scrollbar_reserve = 18
            usable = max(100, total_width - scrollbar_reserve)
            
            min_widths = [self.column_configs.get(c, {}).get("width", 100) for c in visible_columns]
            sum_min = sum(min_widths) if min_widths else 1
            
            raw_widths = [usable * (wmin / sum_min) for wmin in min_widths]
            widths = [int(w) for w in raw_widths]
            current_total = sum(widths)
            diff = usable - current_total
            
            i = 0
            n = len(widths)
            while diff != 0 and n > 0:
                idx = i % n
                if diff > 0:
                    widths[idx] += 1
                    diff -= 1
                else:
                    if widths[idx] > 0:
                        widths[idx] -= 1
                        diff += 1
                i += 1
            
            for col, w in zip(visible_columns, widths):
                try:
                    self.tree.column(col, width=w, stretch=True)
                except Exception:
                    pass
        except Exception:
            pass
#endregion

# ============================================================================
# PERSONAL DATABASE WINDOW
# ============================================================================
#region personal database window
class Personal_db_window(ctk.CTkToplevel):
    """Personal database management window with zoomable timeline"""
    
    def __init__(self, parent, user):
        super().__init__(parent)
        self.title("Personal Database Manager")
        self.transient(parent)
        self.parent = parent
        self.user = user
        self.current_date = datetime.date.today()
        self.zoom_level = 1.0  # 1.0 = normal, 2.0 = 2x zoom, etc.
        self.db = DatabaseManager(DB_FILE)
        # Initialize personal database
        personal_db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            f"Database/{user.lower()}_records.db"
        )
        
        # Import PersonalDatabaseManager at the top if not already imported
        from Database.database import PersonalDatabaseManager
        
        try:
            self.personal_db = PersonalDatabaseManager(path_to_person_database = personal_db_path)
        except Exception as e:
            print(f"Error loading personal database: {e}")
            self.personal_db = None
    
        # Set fullscreen
        self.update_idletasks()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        try:
            self.attributes("-fullscreen", True)
        except Exception:
            self.geometry(f"{screen_width}x{screen_height}+0+0")
    
        self.update_idletasks()
        self.lift()
        self.focus_force()
        
        def do_grab():
            try:
                self.grab_set()
            except Exception as e:
                print(f"Could not grab focus: {e}")
        self.after(100, do_grab)
        
        self._setup_ui()
        self.bind("<Escape>", lambda e: self.destroy())
        self.load_timeline_data()

    def _setup_ui(self):
        """Setup the personal database UI"""
        # Configure grid
        self.grid_rowconfigure(0, weight=0)  # Title
        self.grid_rowconfigure(1, weight=0)  # Date selector
        self.grid_rowconfigure(2, weight=1)  # Timeline
        self.grid_rowconfigure(3, weight=0)  # Controls
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        ctk.CTkLabel(
            self, 
            text=f"{self.user}'s Personal Database", 
            font=("Arial", 32, "bold")
        ).grid(row=0, column=0, pady=(20, 10), sticky="ew")
        
        # Date selector frame
        date_frame = ctk.CTkFrame(self, fg_color="transparent")
        date_frame.grid(row=1, column=0, pady=10, sticky="ew")
        
        ctk.CTkButton(
            date_frame,
            text="◄ Previous Day",
            command=self.previous_day,
            width=180,
            height=50,
            font=("Arial", 18)
        ).pack(side="left", padx=(40, 10))
        
        self.date_label = ctk.CTkLabel(
            date_frame,
            text=self.current_date.strftime("%A, %B %d, %Y"),
            font=("Arial", 22, "bold")
        )
        self.date_label.pack(side="left", expand=True)
        
        ctk.CTkButton(
            date_frame,
            text="Next Day ►",
            command=self.next_day,
            width=180,
            height=50,
            font=("Arial", 18)
        ).pack(side="right", padx=(10, 40))
        
        # Timeline frame
        timeline_frame = ctk.CTkFrame(self, corner_radius=10)
        timeline_frame.grid(row=2, column=0, sticky="nsew", padx=40, pady=20)
        timeline_frame.grid_rowconfigure(0, weight=1)
        timeline_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas with scrollbar for timeline
        self.timeline_canvas = tk.Canvas(
            timeline_frame,
            bg="#2b2b2b",
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            timeline_frame,
            orient="horizontal",
            command=self.timeline_canvas.xview
        )
        self.timeline_canvas.configure(xscrollcommand=scrollbar.set)
        
        self.timeline_canvas.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 5))
        scrollbar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Bind mouse wheel for scrolling
        self.timeline_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.timeline_canvas.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
        self.timeline_canvas.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down
        
        # Control buttons frame
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.grid(row=3, column=0, pady=(0, 30), sticky="ew")
        
        ctk.CTkButton(
            controls_frame,
            text="Zoom In (+)",
            command=self.zoom_in,
            width=140,
            height=55,
            font=("Arial", 18)
        ).pack(side="left", padx=(40, 10))
        
        ctk.CTkButton(
            controls_frame,
            text="Zoom Out (-)",
            command=self.zoom_out,
            width=140,
            height=55,
            font=("Arial", 18)
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            controls_frame,
            text="Reset Zoom",
            command=self.reset_zoom,
            width=140,
            height=55,
            font=("Arial", 18)
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            controls_frame,
            text="Today",
            command=self.goto_today,
            width=140,
            height=55,
            font=("Arial", 18),
            fg_color="#22c55e"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            controls_frame,
            text="Close",
            command=self.destroy,
            width=140,
            height=55,
            font=("Arial", 18),
            fg_color="#b22222"
        ).pack(side="right", padx=(10, 40))
    
    def load_timeline_data(self):
        """Load user's activity data and prescriptions for the selected date"""
        self.activities = []
        self.prescriptions = []
        
        if not self.personal_db:
            self.draw_timeline()
            return
        
        try:
            # get_personal_data returns (hist_logs, prescript_logs)
            # hist_logs format: list of (barcode, dname, when_taken, dose)
            # prescript_logs format: list of (barcode, dname, dosage, time, leeway)
            
            hist_logs, prescript_logs = self.personal_db.get_personal_data(self.current_date.strftime("%Y-%m-%d"))

            ###debug
            print(hist_logs, prescript_logs)
            
            ###

            # Process history logs (actual usage)
            for log in hist_logs:
                try:
                    if len(log) < 4:
                        continue
                        
                    barcode = log[0]
                    name = log[1]
                    when_taken = log[2]
                    dose = log[3]
                    
                    # Parse timestamp
                    try:
                        dt = datetime.datetime.strptime(when_taken, "%Y-%m-%d %H:%M:%S")
                    except:
                        try:
                            dt = datetime.datetime.fromisoformat(when_taken)
                        except:
                            continue
                    
                    # Only include if it's on the current date
                    if dt.date() == self.current_date:
                        self.activities.append({
                            'time': dt.time(),
                            'name': name,
                            'amount': dose,
                            'barcode': barcode
                        })
                except Exception as e:
                    print(f"Error processing history log: {e}, log: {log}")
                    continue
            
            # Process prescription logs (scheduled medications)
            for prescription in prescript_logs:
                try:
                    if len(prescription) < 5:
                        continue
                        
                    barcode = prescription[0]
                    name = prescription[1]
                    dosage = prescription[2]
                    time_str = prescription[3]
                    leeway = prescription[4]
                    
                    # Parse time (HH:MM:SS format)
                    if time_str:
                        try:
                            # Handle different time formats
                            if isinstance(time_str, datetime.time):
                                scheduled_time = time_str
                            elif ':' in str(time_str):
                                time_parts = str(time_str).split(':')
                                scheduled_time = datetime.time(
                                    int(time_parts[0]),
                                    int(time_parts[1]),
                                    int(time_parts[2]) if len(time_parts) > 2 else 0
                                )
                            else:
                                scheduled_time = datetime.time(9, 0, 0)
                        except Exception as e:
                            print(f"Error parsing time: {e}")
                            scheduled_time = datetime.time(9, 0, 0)
                    else:
                        scheduled_time = datetime.time(9, 0, 0)
                    
                    self.prescriptions.append({
                        'time': scheduled_time,
                        'name': name,
                        'dosage': dosage,
                        'barcode': barcode,
                        'leeway': int(leeway) if leeway else 60
                    })
                except Exception as e:
                    print(f"Error processing prescription: {e}, prescription: {prescription}")
                    continue
                
        except Exception as e:
            print(f"Error loading timeline data: {e}")
            import traceback
            traceback.print_exc()
    
        self.draw_timeline()

    def draw_timeline(self):
        """Draw the 24-hour timeline with activities and prescriptions"""
        self.timeline_canvas.delete("all")
        
        canvas_width = self.timeline_canvas.winfo_width()
        canvas_height = self.timeline_canvas.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = 1200
        if canvas_height <= 1:
            canvas_height = 400
        
        # Calculate dimensions
        hour_width = 120 * self.zoom_level
        total_width = hour_width * 24
        timeline_y = canvas_height // 2
        
        # Update scroll region
        self.timeline_canvas.configure(scrollregion=(0, 0, total_width, canvas_height))
        
        # Draw hour markers
        for hour in range(25):  # 0-24
            x = hour * hour_width
            
            # Hour line
            self.timeline_canvas.create_line(
                x, timeline_y - 30, x, timeline_y + 30,
                fill="#5F84C8" if hour % 3 == 0 else "#4a4a4a",
                width=3 if hour % 3 == 0 else 1
            )
            
            # Hour label
            label = f"{hour:02d}:00"
            self.timeline_canvas.create_text(
                x, timeline_y + 50,
                text=label,
                fill="white",
                font=("Arial", int(14 * min(self.zoom_level, 1.5)), "bold" if hour % 3 == 0 else "normal")
            )
        
        # Draw main timeline
        self.timeline_canvas.create_line(
            0, timeline_y, total_width, timeline_y,
            fill="#5F84C8",
            width=4
        )
        
        # Draw prescription markers (below timeline) with improved rendering
        for prescription in self.prescriptions:
            time_obj = prescription['time']
            hour = time_obj.hour
            minute = time_obj.minute
            
            # Calculate x position
            x = (hour + minute / 60.0) * hour_width
            
            # Draw prescription window (leeway area) - semi-transparent background
            leeway_minutes = prescription['leeway']
            leeway_width = (leeway_minutes / 60.0) * hour_width
            
            # Background box for prescription
            box_height = 60
            box_top = timeline_y + 45
            
            # Draw subtle background
            self.timeline_canvas.create_rectangle(
                x - leeway_width / 2, box_top,
                x + leeway_width / 2, box_top + box_height,
                fill="#1e3a5f",
                outline="",
                stipple="gray25"
            )
            
            # Draw main prescription box (cleaner, more compact)
            box_width = max(80 * min(self.zoom_level, 2.0), 40)
            box_inner_height = 35
            box_y = timeline_y + 60
            
            self.timeline_canvas.create_rectangle(
                x - box_width/2, box_y,
                x + box_width/2, box_y + box_inner_height,
                fill="#3b82f6",
                outline="#60a5fa",
                width=2
            )
            
            # Draw Rx symbol with better sizing
            rx_font_size = int(12 * min(self.zoom_level, 2.0))
            self.timeline_canvas.create_text(
                x, box_y + box_inner_height/2,
                text="Rx",
                fill="white",
                font=("Arial", rx_font_size, "bold")
            )
            
            # Draw prescription info below box (only if zoomed in enough)
            if self.zoom_level >= 0.8:
                info_y = box_y + box_inner_height + 10
                
                # Name on first line
                self.timeline_canvas.create_text(
                    x, info_y,
                    text=prescription['name'],
                    fill="#60a5fa",
                    font=("Arial", int(10 * min(self.zoom_level, 1.5)), "bold"),
                    justify="center",
                    width=leeway_width * 0.9
                )
                
                # Dosage on second line
                self.timeline_canvas.create_text(
                    x, info_y + 15,
                    text=f"{prescription['dosage']} dose",
                    fill="#93c5fd",
                    font=("Arial", int(9 * min(self.zoom_level, 1.5))),
                    justify="center"
                )
                
                # Time label above box
                time_str = time_obj.strftime("%H:%M")
                self.timeline_canvas.create_text(
                    x, box_y - 8,
                    text=time_str,
                    fill="#94a3b8",
                    font=("Arial", int(9 * min(self.zoom_level, 1.5)))
                )

        # Draw actual usage activities (above timeline) with improved rendering
        for activity in self.activities:
            time_obj = activity['time']
            hour = time_obj.hour
            minute = time_obj.minute
            
            # Calculate x position
            x = (hour + minute / 60.0) * hour_width
            
            color = "#f59e0b"
            symbol = "−"
            matched_prescription = False
            
            # Check for prescription match
            for prescription in self.prescriptions:
                presc_minutes = prescription['time'].hour * 60 + prescription['time'].minute
                activity_minutes = time_obj.hour * 60 + time_obj.minute
                time_diff = abs(activity_minutes - presc_minutes)
                
                try:
                    activity_dose = int(activity['amount'])
                    prescription_dose = int(prescription['dosage'])
                    
                    if (time_diff <= prescription['leeway'] and 
                        activity['name'] == prescription['name'] and
                        activity_dose == prescription_dose):
                        matched_prescription = True
                        color = "#22c55e"
                        symbol = "✓"
                        break
                except (ValueError, TypeError):
                    if (time_diff <= prescription['leeway'] and 
                        activity['name'] == prescription['name']):
                        matched_prescription = True
                        color = "#22c55e"
                        symbol = "✓"
                        break
            
            # Draw activity box (cleaner design)
            box_width = max(80 * min(self.zoom_level, 2.0), 40)
            box_height = 35
            box_y = timeline_y - 80
            
            # Main activity box
            self.timeline_canvas.create_rectangle(
                x - box_width/2, box_y,
                x + box_width/2, box_y + box_height,
                fill=color,
                outline="white",
                width=2
            )
            
            # Symbol in center
            symbol_font_size = int(14 * min(self.zoom_level, 2.0))
            self.timeline_canvas.create_text(
                x, box_y + box_height/2,
                text=symbol,
                fill="white",
                font=("Arial", symbol_font_size, "bold")
            )
            
            # Match checkmark badge (if matched)
            if matched_prescription:
                badge_size = 12 * min(self.zoom_level, 1.5)
                badge_x = x + box_width/2 + 8
                badge_y = box_y - 8
                
                # Badge circle
                self.timeline_canvas.create_oval(
                    badge_x - badge_size, badge_y - badge_size,
                    badge_x + badge_size, badge_y + badge_size,
                    fill="#22c55e",
                    outline="white",
                    width=2
                )
                
                # Checkmark
                self.timeline_canvas.create_text(
                    badge_x, badge_y,
                    text="✓",
                    fill="white",
                    font=("Arial", int(10 * min(self.zoom_level, 1.5)), "bold")
                )
            
            # Activity info above box (only if zoomed in enough)
            if self.zoom_level >= 0.8:
                info_y = box_y - 10
                
                # Time at top
                time_str = time_obj.strftime("%H:%M")
                self.timeline_canvas.create_text(
                    x, info_y,
                    text=time_str,
                    fill="#94a3b8",
                    font=("Arial", int(9 * min(self.zoom_level, 1.5)))
                )
                
                # Name below time
                self.timeline_canvas.create_text(
                    x, info_y - 18,
                    text=activity['name'],
                    fill="white",
                    font=("Arial", int(10 * min(self.zoom_level, 1.5)), "bold"),
                    justify="center",
                    width=hour_width * 0.8
                )
                
                # Amount taken
                try:
                    amount_str = str(activity['amount'])
                except:
                    amount_str = "?"
                
                self.timeline_canvas.create_text(
                    x, info_y - 33,
                    text=f"{amount_str} taken",
                    fill="#d1d5db",
                    font=("Arial", int(9 * min(self.zoom_level, 1.5))),
                    justify="center"
                )
        
        # Draw legend with cleaner layout
        legend_y = 20
        legend_x = 20
        
        # Legend background
        self.timeline_canvas.create_rectangle(
            legend_x - 10, legend_y - 15,
            legend_x + 620, legend_y + 35,
            fill="#1a1a1a",
            outline="#4a4a4a",
            width=1
        )
        
        # Legend title
        self.timeline_canvas.create_text(
            legend_x, legend_y,
            text="Legend:",
            fill="white",
            font=("Arial", 12, "bold"),
            anchor="w"
        )
        
        # Prescription indicator
        self.timeline_canvas.create_rectangle(
            legend_x + 70, legend_y - 6,
            legend_x + 90, legend_y + 6,
            fill="#3b82f6",
            outline="white",
            width=2
        )
        self.timeline_canvas.create_text(
            legend_x + 100, legend_y,
            text="Scheduled",
            fill="#60a5fa",
            font=("Arial", 11),
            anchor="w"
        )
        
        # Usage indicator
        self.timeline_canvas.create_rectangle(
            legend_x + 210, legend_y - 6,
            legend_x + 230, legend_y + 6,
            fill="#f59e0b",
            outline="white",
            width=2
        )
        self.timeline_canvas.create_text(
            legend_x + 240, legend_y,
            text="Taken",
            fill="white",
            font=("Arial", 11),
            anchor="w"
        )
        
        # Matched indicator
        self.timeline_canvas.create_rectangle(
            legend_x + 320, legend_y - 6,
            legend_x + 340, legend_y + 6,
            fill="#22c55e",
            outline="white",
            width=2
        )
        self.timeline_canvas.create_text(
            legend_x + 350, legend_y,
            text="Matched",
            fill="#22c55e",
            font=("Arial", 11),
            anchor="w"
        )
        
        # Checkmark explanation
        badge_x = legend_x + 450
        self.timeline_canvas.create_oval(
            badge_x - 8, legend_y - 8,
            badge_x + 8, legend_y + 8,
            fill="#22c55e",
            outline="white",
            width=1
        )
        self.timeline_canvas.create_text(
            badge_x, legend_y,
            text="✓",
            fill="white",
            font=("Arial", 10, "bold")
        )
        self.timeline_canvas.create_text(
            badge_x + 20, legend_y,
            text="= Match",
            fill="#22c55e",
            font=("Arial", 11),
            anchor="w"
        )
    
        # Debug: print what we're drawing
        print(f"Drawing timeline with {len(self.prescriptions)} prescriptions and {len(self.activities)} activities")
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 4 or event.delta > 0:
            self.timeline_canvas.xview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.timeline_canvas.xview_scroll(1, "units")
    
    def zoom_in(self):
        """Increase zoom level"""
        if self.zoom_level < 5.0:
            self.zoom_level *= 1.5
            self.draw_timeline()
    
    def zoom_out(self):
        """Decrease zoom level"""
        if self.zoom_level > 0.3:
            self.zoom_level /= 1.5
            self.draw_timeline()
    
    def reset_zoom(self):
        """Reset zoom to default"""
        self.zoom_level = 1.0
        self.draw_timeline()
    
    def previous_day(self):
        """Go to previous day"""
        self.current_date -= datetime.timedelta(days=1)
        self.date_label.configure(text=self.current_date.strftime("%A, %B %d, %Y"))
        self.load_timeline_data()
    
    def next_day(self):
        """Go to next day"""
        self.current_date += datetime.timedelta(days=1)
        self.date_label.configure(text=self.current_date.strftime("%A, %B %d, %Y"))
        self.load_timeline_data()
    
    def goto_today(self):
        """Jump to today's date"""
        self.current_date = datetime.date.today()
        self.date_label.configure(text=self.current_date.strftime("%A, %B %d, %Y"))
        self.load_timeline_data()
#endregion

# ============================================================================
# VIRTUAL KEYBOARD
# ============================================================================
#region virtual keyboard
class VirtualKeyboard(ctk.CTkToplevel):
    """Virtual keyboard for touch screen input"""
    
    def __init__(self, parent, title="Virtual Keyboard", prompt="Enter text:", initial_text=""):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.resizable(False, False)
        
        self.result = {"value": None}
        self.shift_active = False
        self.caps_lock = False
        
        self._setup_ui(prompt, initial_text)
        self._center_window(parent)
        
        self.grab_set()
        self.focus_force()
    
    def _setup_ui(self, prompt, initial_text):
        """Setup keyboard UI"""
        # Prompt label
        ctk.CTkLabel(
            self, 
            text=prompt, 
            anchor="w", 
            font=("Arial", 22)
        ).pack(padx=25, pady=(22, 12))
        
        # Text entry
        self.entry_var = tk.StringVar(value=initial_text)
        self.entry = ctk.CTkEntry(
            self,
            textvariable=self.entry_var,
            width=800,
            height=60,
            font=("Arial", 20)
        )
        self.entry.pack(padx=25, pady=(0, 15))
        self.entry.focus_set()
        
        # Keyboard frame
        keyboard_frame = ctk.CTkFrame(self, corner_radius=6)
        keyboard_frame.pack(padx=25, pady=(0, 15), fill="both", expand=True)
        
        # Define keyboard layout (QWERTY)
        self.keys_layout = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'"],
            ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/']
        ]
        
        # Special keys shifted versions
        self.shift_map = {
            '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
            '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
            '-': '_', '=': '+', '[': '{', ']': '}', ';': ':',
            "'": '"', ',': '<', '.': '>', '/': '?'
        }
        
        # Create keyboard rows
        for row_idx, row in enumerate(self.keys_layout):
            row_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
            row_frame.pack(pady=5)
            
            # Add shift for third row
            if row_idx == 2:
                shift_btn = ctk.CTkButton(
                    row_frame,
                    text="⇧ Shift",
                    command=self.toggle_shift,
                    width=90,
                    height=65,
                    font=("Arial", 16)
                )
                shift_btn.pack(side="left", padx=3)
                self.shift_btn = shift_btn
            
            # Add keys for this row
            for key in row:
                btn = ctk.CTkButton(
                    row_frame,
                    text=key.upper() if self.caps_lock or self.shift_active else key,
                    command=lambda k=key: self.key_press(k),
                    width=65,
                    height=65,
                    font=("Arial", 18, "bold")
                )
                btn.pack(side="left", padx=3)
            
            # Add backspace for first row
            if row_idx == 0:
                backspace_btn = ctk.CTkButton(
                    row_frame,
                    text="⌫",
                    command=self.backspace,
                    width=90,
                    height=65,
                    font=("Arial", 20),
                    fg_color="#dc2626"
                )
                backspace_btn.pack(side="left", padx=3)
        
        # Bottom row with special keys
        bottom_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
        bottom_frame.pack(pady=5)
        
        ctk.CTkButton(
            bottom_frame,
            text="Caps",
            command=self.toggle_caps,
            width=90,
            height=65,
            font=("Arial", 16)
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            bottom_frame,
            text="Space",
            command=lambda: self.key_press(' '),
            width=400,
            height=65,
            font=("Arial", 18)
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            bottom_frame,
            text="Clear",
            command=self.clear_all,
            width=90,
            height=65,
            font=("Arial", 16),
            fg_color="#f59e0b"
        ).pack(side="left", padx=3)
        
        # Action buttons
        action_frame = ctk.CTkFrame(self, corner_radius=6)
        action_frame.pack(pady=(0, 22), padx=25, fill="x")
        
        ctk.CTkButton(
            action_frame,
            text="OK",
            command=self.on_ok,
            width=180,
            height=60,
            font=("Arial", 20),
            fg_color="#22c55e"
        ).pack(side="left", padx=12, pady=12)
        
        ctk.CTkButton(
            action_frame,
            text="Cancel",
            command=self.on_cancel,
            width=180,
            height=60,
            font=("Arial", 20),
            fg_color="gray30"
        ).pack(side="right", padx=12, pady=12)
        
        # Bind Enter and Escape
        self.entry.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.on_cancel())
    
    def key_press(self, key):
        """Handle key press"""
        current = self.entry_var.get()
        
        # Check if we need to use shifted version
        if (self.shift_active or self.caps_lock) and key in self.shift_map:
            key = self.shift_map[key]
        elif self.shift_active or self.caps_lock:
            key = key.upper()
        
        self.entry_var.set(current + key)
        
        # Reset shift after key press (but not caps lock)
        if self.shift_active:
            self.shift_active = False
            self._update_key_display()
    
    def backspace(self):
        """Remove last character"""
        current = self.entry_var.get()
        self.entry_var.set(current[:-1])
    
    def clear_all(self):
        """Clear entire entry"""
        self.entry_var.set("")
    
    def toggle_shift(self):
        """Toggle shift state"""
        self.shift_active = not self.shift_active
        self._update_key_display()
    
    def toggle_caps(self):
        """Toggle caps lock"""
        self.caps_lock = not self.caps_lock
        self.shift_active = False
        self._update_key_display()
    
    def _update_key_display(self):
        """Update keyboard key labels based on shift/caps state"""
        # This would update all key button texts - simplified for now
        # In a full implementation, you'd store references to all key buttons
        # and update their text here
        pass
    
    def on_ok(self):
        """Handle OK button"""
        self.result["value"] = self.entry_var.get().strip()
        try:
            self.grab_release()
        except:
            pass
        self.destroy()
    
    def on_cancel(self):
        """Handle Cancel button"""
        self.result["value"] = None
        try:
            self.grab_release()
        except:
            pass
        self.destroy()
    
    def _center_window(self, parent):
        """Center window on parent"""
        self.update_idletasks()
        
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        window_width = self.winfo_reqwidth()
        window_height = self.winfo_reqheight()
        
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    @staticmethod
    def get_input(parent, title="Virtual Keyboard", prompt="Enter text:", initial_text=""):
        """Static method to show keyboard and get input"""
        keyboard = VirtualKeyboard(parent, title, prompt, initial_text)
        parent.wait_window(keyboard)
        return keyboard.result["value"]
#endregion

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    app = BarcodeViewer()
    app.mainloop()