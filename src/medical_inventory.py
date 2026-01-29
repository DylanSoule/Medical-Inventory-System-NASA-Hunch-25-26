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
        
        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            frame,
            textvariable=self.search_var,
            placeholder_text="Search all fields...",
            height=50,
            font=("Arial", 20)
        )
        search_entry.pack(fill="x")
        search_entry.bind("<KeyRelease>", self.apply_search_filter)

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
        
        # Get deletion reason
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.transient(self)
        dlg.resizable(False, False)
        
        ctk.CTkLabel(dlg, text=prompt, anchor="w", font=("Arial", 22)).pack(padx=25, pady=(22, 12))
        
        entry_var = tk.StringVar()
        entry = ctk.CTkEntry(dlg, textvariable=entry_var, width=600, height=55, font=("Arial", 20))
        entry.pack(padx=25, pady=(0, 22))
        
        result = {"value": None}
        
        def on_ok_del(event=None):
            val = entry_var.get().strip()
            if val == "":
                return
            result["value"] = val
            try:
                dlg.grab_release()
            except:
                pass
            dlg.destroy()
        
        def on_cancel_del(event=None):
            try:
                dlg.grab_release()
            except:
                pass
            dlg.destroy()
        
        btn_frame = ctk.CTkFrame(dlg, corner_radius=6)
        btn_frame.pack(pady=(0, 22), padx=18, fill="x")
        ctk.CTkButton(btn_frame, text="OK", command=on_ok_del, width=160, height=55, 
                     font=("Arial", 20)).pack(side="left", padx=12, pady=12)
        ctk.CTkButton(btn_frame, text="Cancel", command=on_cancel_del, width=160, height=55, 
                     font=("Arial", 20), fg_color="gray30").pack(side="left", padx=12, pady=12)
        
        entry.bind("<Return>", on_ok_del)
        dlg.bind("<Escape>", on_cancel_del)
        
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (dlg.winfo_reqwidth() // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (dlg.winfo_reqheight() // 2)
        dlg.geometry(f"+{x}+{y}")
        
        def do_grab():
            try:
                dlg.grab_set()
                entry.focus_set()
            except:
                pass
        dlg.after(50, do_grab)
        
        self.wait_window(dlg)
        reason = result["value"]
        
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
    """Personal database management window"""
    
    def __init__(self, parent, user):
        super().__init__(parent)
        self.title("Personal Database Manager")
        self.transient(parent)
        
        # Set fullscreen
        try:
            self.attributes("-fullscreen", True)
        except Exception:
            try:
                self.state("zoomed")
            except Exception:
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()
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
        
        # Title
        ctk.CTkLabel(self, text=f"{user}'s Personal Database", font=("Arial", 24)).pack(pady=20)
        
        # Calendar frame
        cal_frame = ctk.CTkFrame(self)
        cal_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        # Calendar
        calendar = tkcal.Calendar(
            cal_frame,
            selectmode="day",
            font=("Arial", 20),
            headersforeground="black",
            normalforeground="black",
            normalbackground="white",
            weekendforeground="red",
            othermonthforeground="gray",
            selectforeground="white",
            selectbackground="#5F84C8",
            date_pattern="yyyy-mm-dd"
        )
        calendar.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Close button
        ctk.CTkButton(self, text="Close", command=self.destroy, width=160, height=55, 
                     font=("Arial", 20)).pack(pady=20)
        
        self.bind("<Escape>", lambda e: self.destroy())
#endregion

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    app = BarcodeViewer()
    app.mainloop()