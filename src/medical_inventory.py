import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import os
import sys
from tkinter import simpledialog
import datetime
# Add parent directory to path for imports from Database and src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import facial_recognition as fr
from Database.database import DatabaseManager
from facial_recognition import FaceRecognitionError

# Database file path - store in parent directory
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Database/inventory.db")
REFRESH_INTERVAL = 30000  # milliseconds
# Use CustomTkinter main window for modern look
ctk.set_appearance_mode("Dark")         # "Dark", "Light", or "System"
ctk.set_default_color_theme("dark-blue") # built-in themes: "blue", "green", "dark-blue"

class BarcodeViewer(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Initialize database
        self.db = DatabaseManager(DB_FILE)
        
        # Start preloading facial recognition immediately
        self._start_preloading()
        
        # Start background camera recovery monitor
        self._start_camera_recovery_monitor()

        self.title("Medical Inventory System")
        # start fullscreen
        try:
            # prefer true fullscreen (hides window decorations)
            self.attributes("-fullscreen", True)
        except Exception:
            # fallback to maximized state where available
            try:
                self.state("zoomed")
            except Exception:
                self.geometry("1200x800")

        # larger default styling for readability on fullscreen
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 28))
        style.configure("TButton", font=("Arial", 24), padding=20)
        style.configure("Treeview", font=("Arial", 22), rowheight=55)
        style.configure("Treeview.Heading", font=("Arial", 24, "bold"))

        # allow toggling fullscreen with F11 and exit fullscreen with Escape
        self.bind("<F11>", lambda e: self.attributes("-fullscreen", not self.attributes("-fullscreen")))
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))

        # keep current log path on the instance
        # self.log_file = LOG_FILE

        # Title (use CTkLabel for modern appearance)
        ctk.CTkLabel(self, text="Medical Inventory System", font=("Arial", 40, "bold")).pack(pady=25)

        # Main frame containing sidebar (left) and content (right)
        main_frame = ctk.CTkFrame(self, corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=18, pady=(10,25))

        # Sidebar on the left with buttons, search and filters
        sidebar = ctk.CTkFrame(main_frame, width=420, corner_radius=8)
        sidebar.pack(side="left", fill="y", padx=(18,25), pady=18)

        # Search
        ctk.CTkLabel(sidebar, text="Search", anchor="w", font=("Arial", 22)).pack(padx=25, pady=(25,10), fill="x")
        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(sidebar, textvariable=self.search_var, placeholder_text="Search all fields...", width=370, height=50, font=("Arial", 20))
        search_entry.pack(padx=25, pady=(0,18))
        search_entry.bind("<KeyRelease>", self.apply_search_filter)

        # Filter
        ctk.CTkLabel(sidebar, text="Filters", anchor="w", font=("Arial", 22)).pack(padx=25, pady=(18,10), fill="x")

        self.filter_var = tk.StringVar(value="All")
        filter_opts = ["All", "Expiring Soon", "Expired"]
        ctk.CTkOptionMenu(sidebar, values=filter_opts, variable=self.filter_var, width=370, height=50, font=("Arial", 20), command=lambda v: self.apply_search_filter()).pack(padx=25, pady=(0,18))

        # Example checkbox (e.g., show only low stock)
        self.low_stock_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(sidebar, text="Show low stock only", variable=self.low_stock_var, font=("Arial", 20), command=self.apply_search_filter).pack(padx=25, pady=(10,18))

        # Column visibility controls
        ctk.CTkLabel(sidebar, text="Show Columns", anchor="w", font=("Arial", 22)).pack(padx=25, pady=(18,10), fill="x")

    #region ######################## Column configs

            # Create Treeview (table) with user column inside content frame
        columns = ("drug", "barcode", "est_amount", "exp_date", "type_", "dose_size", "item_type", "item_loc")

            # Track column visibility
        self.column_visibility = {
            "drug": tk.BooleanVar(value=True),
            "barcode": tk.BooleanVar(value=True),
            "est_amount": tk.BooleanVar(value=True),
            "exp_date": tk.BooleanVar(value=True),
            "type_": tk.BooleanVar(value=True),
            "dose_size": tk.BooleanVar(value=True),
            "item_type": tk.BooleanVar(value=True),
            "item_loc": tk.BooleanVar(value=True)
        }
        
            # Column labels for display
        column_labels = {
            "drug": "Drug",
            "barcode": "Barcode",
            "est_amount": "Amt~",
            "exp_date": "Expiration",
            "type_": "Type",
            "dose_size": "Dose Size",
            "item_type": "Item Type",
            "item_loc": "Location (WIP)"
        }

            # Store column configurations
        self.column_configs = {
            "drug": {"text": "Drug", "width": 220},
            "barcode": {"text": "Barcode", "width": 170},
            "est_amount": {"text": "Amt~", "width": 100},
            "exp_date": {"text": "Expiration", "width": 140},
            "type_": {"text": "Type", "width": 120},
            "dose_size": {"text": "Dose Size", "width": 140},
            "item_type": {"text": "Item Type", "width": 140},
            "item_loc": {"text": "Location (WIP)", "width": 100}
        }
            # Create checkboxes for each column
        columns_frame = ctk.CTkFrame(sidebar, corner_radius=6)
        columns_frame.pack(padx=25, pady=(0,18), fill="x")
        
        for col_id, label in column_labels.items():
            ctk.CTkCheckBox(
                columns_frame, 
                text=label, 
                variable=self.column_visibility[col_id],
                font=("Arial", 18),
                command=self.update_column_visibility
            ).pack(padx=12, pady=5, anchor="w")

    #endregion
    
    # Vertical button group in sidebar
        btns_frame = ctk.CTkFrame(sidebar, corner_radius=6)
        btns_frame.pack(padx=25, pady=(25,25), fill="x")

# Container to hold button + overlay indicator
        btn_container = ctk.CTkFrame(btns_frame, corner_radius=0, fg_color="transparent")
        btn_container.pack(pady=(12, 12))

    #region ######################## Log Scan Button with Status Indicator
        # Log Scan button (exact width 350px)
        self.log_scan_btn = ctk.CTkButton(
                btn_container,
                text="Log Item Use (WIP)",
                state="enabled",
                command=self.log_scan,
                width=350,
                height=60,
                font=("Arial", 22)
        )
        self.log_scan_btn.pack()

        # Status indicator for Log Scan button
        self.log_scan_indicator = ctk.CTkFrame(
                btn_container,
                width=18,
                height=18,
                corner_radius=12,
                fg_color="#94a3b8",        # circle color
                bg_color="#1f538d",
        )
        self.log_scan_indicator.pack_propagate(False)

        # Place it over the right edge of the button
        self.log_scan_indicator.place(in_=self.log_scan_btn, relx=1.0, rely=0.5, anchor="e", x=-12)

        # Change indicator color on button hover
        def on_enter_log(_):
            self.log_scan_indicator.configure(bg_color="#14375e")
        def on_leave_log(_):
            self.log_scan_indicator.configure(bg_color="#1f538d")

        self.log_scan_btn.bind("<Enter>", on_enter_log)
        self.log_scan_btn.bind("<Leave>", on_leave_log)

        # Make sure it renders above the button
        self.log_scan_indicator.tkraise()
    #endregion

    #region ######################## personal DB Button with Status Indicator
        self.personal_db_btn = ctk.CTkButton(
            btn_container,
            text="View Personal Database (WIP)",
            command=self.personal_db,
            state="enabled",
            width=350,
            height=60,
            font=("Arial", 22)
        )
        self.personal_db_btn.pack(pady=12)
        
        # Status indicator for Personal DB button
        self.personal_db_indicator = ctk.CTkFrame(
                btn_container,
                width=18,
                height=18,
                corner_radius=12,
                fg_color="#94a3b8",        # circle color
                bg_color="#1f538d",
        )
        self.personal_db_indicator.pack_propagate(False)

        # Place it over the right edge of the button
        self.personal_db_indicator.place(in_=self.personal_db_btn, relx=1.0, rely=0.5, anchor="e", x=-12)
        
        # Change indicator color on button hover
        def on_enter_personal(_):
            self.personal_db_indicator.configure(bg_color="#14375e")
        def on_leave_personal(_):
            self.personal_db_indicator.configure(bg_color="#1f538d")

        self.personal_db_btn.bind("<Enter>", on_enter_personal)
        self.personal_db_btn.bind("<Leave>", on_leave_personal)

        # Make sure it renders above the button
        self.personal_db_indicator.tkraise()
    #endregion

        ctk.CTkButton(btns_frame, text="Delete Selected", command=self.delete_selected, width=350, height=60, font=("Arial", 22)).pack(pady=12)
        ctk.CTkButton(btns_frame, text="View History", command=self.show_history, width=350, height=60, font=("Arial", 22)).pack(pady=12)
        ctk.CTkButton(btns_frame, text="Quit", command=self.destroy, width=350, height=60, font=("Arial", 22), fg_color="#b22222").pack(pady=12)

        # Content frame (right) for the treeview / main table
        content_frame = ctk.CTkFrame(main_frame, corner_radius=6)
        content_frame.pack(side="left", fill="both", expand=True, padx=(0,18), pady=18)

        #keep extended selectmode but we intercept clicks to allow toggle-without-ctrl
        self.tree = ttk.Treeview(content_frame, columns=columns, show="headings", selectmode="extended")
        
        # Configure all columns initially
        for col_id, config in self.column_configs.items():
            self.tree.heading(col_id, text=config["text"])
            self.tree.column(col_id, width=config["width"])

        # Adjust columns automatically when tree resizes
        self.tree.bind("<Configure>", self._on_tree_configure)
 
        # Bind left-click to toggle selection on rows without requiring Ctrl/Shift
        # Clicking on a row toggles it in the selection set; clicking empty area clears selection.
        self.tree.bind("<Button-1>", self._on_tree_click)

        # Add scrollbar (ttk scrollbar looks fine beside CTk styled widgets)
        scroll = ttk.Scrollbar(content_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(fill="both", expand=True, side="left", padx=(18, 0), pady=(18,25))
        scroll.pack(fill="y", side="right", padx=(0, 18), pady=(18,25))

        # Load data and start auto-refresh
        self.load_data()
        # Initial column width adjustment after UI is fully loaded
        self.after(500, lambda: self._adjust_column_widths([c for c, v in self.column_visibility.items() if v.get()]))
        self.after(REFRESH_INTERVAL, self.refresh_data)
    #region ######################## Personal DB
    def personal_db(self):
        """Placeholder for personal database viewing functionality (WIP)"""
        user=self.scan_face(scan_text="access personal database", btn="personal_db_btn", btn_text="View Personal Database")
        if user is None or user == "":
            return
        pass
    #endregion
    def apply_search_filter(self, event=None):
        """
        Apply search and filter UI to the cached DB rows and populate the treeview.
        Filters available:
         - search text (matches drug, barcode, type, dose_size, or item_type)
         - filter_var: "All", "Expiring Soon", "Expired"
         - low_stock_var checkbox (threshold)
        Results are sorted alphabetically by drug name.
        """
        # clear view
        self.tree.delete(*self.tree.get_children())

        rows = getattr(self, "_all_rows", None)
        if rows is None:
            # fallback to pulling directly
            try:
                rows = list(self.db.pull_data("drugs_in_inventory"))
            except Exception:
                rows = []

        q = (self.search_var.get() or "").strip().lower()
        mode = (self.filter_var.get() or "All")
        low_only = bool(self.low_stock_var.get())
        low_threshold = 20  # example threshold for low stock
        now = datetime.date.today()

        def parse_date(d):
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
            # last resort: try ISO parse
            try:
                return datetime.date.fromisoformat(s)
            except Exception:
                return None

        # Collect filtered rows before inserting
        filtered_rows = []

        for row in rows:
            # Normalize DB row into (barcode, drug, est_amount, exp_date, type_, dose_size, item_type, item_loc)
            try:
                barcode, drug, est_amount, exp_date_raw, type_, dose_size, item_type, item_loc = row[0], row[1], row[2], row[3], row[4], row[6], row[5], row[7]
            except Exception:
                # fallback: use positional mapping if shape differs
                vals = list(row)
                barcode = vals[0] if len(vals) > 0 else ""
                drug = vals[1] if len(vals) > 1 else ""
                est_amount = vals[2] if len(vals) > 2 else ""
                exp_date_raw = vals[3] if len(vals) > 3 else None
                type_ = vals[4] if len(vals) > 4 else ""
                dose_size = vals[6] if len(vals) > 5 else ""
                item_type = vals[5] if len(vals) > 6 else ""
                item_loc = vals[7] if len(vals) > 7 else ""

            # Search filter - search across all text fields
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
                    # if amount not parseable, exclude from low-stock view
                    continue
                if amt > low_threshold:
                    continue

            # Expiration filters
            exp_date = parse_date(exp_date_raw)
            if mode == "Expired":
                if not exp_date or exp_date >= now:
                    continue
            elif mode == "Expiring Soon":
                if not exp_date:
                    continue
                delta = (exp_date - now).days
                if delta < 0 or delta > 30:
                    continue

            # Display order: (drug, barcode, est_amount, exp_date, type_, dose_size, item_type)
            display_row = (drug, barcode, est_amount, exp_date_raw, type_, dose_size, item_type, item_loc)
            filtered_rows.append(display_row)

        # Sort alphabetically by drug name (first column in display_row)
        filtered_rows.sort(key=lambda x: str(x[0]).lower())

        # Insert sorted rows into treeview
        for display_row in filtered_rows:
            self.tree.insert("", "end", values=display_row)
#
    def show_popup(self, title, message, popup_type="info"):
        """Show a custom CTk popup dialog matching the app's modern style.
        popup_type: 'info', 'error', or 'warning'
        """
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("520x240")
        popup.resizable(False, False)
        
        # Wait for window to be ready before adding content
        popup.after(10, lambda: self._setup_popup_content(popup, title, message, popup_type))
        
        # Center dialog over parent
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 260
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 120
        popup.geometry(f"520x240+{x}+{y}")
        
        popup.transient(self)
        popup.grab_set()
        
        # Wait for popup to close
        self.wait_window(popup)
    
    def _setup_popup_content(self, popup, title, message, popup_type):
        """Setup popup content after window is ready"""
        # Set colors based on popup type
        if popup_type == "error":
            accent_color = "#dc2626"  # Red
        elif popup_type == "warning":
            
            accent_color = "#f59e0b"  # Amber
        else:
            accent_color = "#3b82f6"  # Blue
        
        # Title with accent color
        ctk.CTkLabel(popup, text=title, font=("Arial", 22, "bold"), text_color=accent_color).pack(pady=(30, 18))
        
        # Message
        ctk.CTkLabel(popup, text=message, font=("Arial", 18), wraplength=460, justify="center").pack(pady=(0, 25))
        
        # OK button
        ctk.CTkButton(popup, text="OK", command=popup.destroy, width=140, height=45, font=("Arial", 18), fg_color=accent_color).pack()
    
    def show_confirm(self, title, message):
        """Show a custom CTk confirmation dialog. Returns True if confirmed, False otherwise."""
        result = {"value": False}
        
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("520x260")
        popup.resizable(False, False)
        
        # Center dialog over parent
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
        
        # Wait for window to be ready before adding content
        def setup_content():
            # Title
            ctk.CTkLabel(popup, text=title, font=("Arial", 22, "bold"), text_color="#3b82f6").pack(pady=(30, 18))
            
            # Message
            ctk.CTkLabel(popup, text=message, font=("Arial", 18), wraplength=460, justify="center").pack(pady=(0, 25))
            
            # Buttons
            btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
            btn_frame.pack()
            
            ctk.CTkButton(btn_frame, text="Yes", command=on_yes, width=120, height=45, font=("Arial", 18)).pack(side="left", padx=12)
            ctk.CTkButton(btn_frame, text="No", command=on_no, width=120, height=45, font=("Arial", 18), fg_color="gray50").pack(side="left", padx=12)
        
        popup.after(10, setup_content)
        popup.bind("<Escape>", lambda e: on_no())
        
        self.wait_window(popup)
        return result["value"]
    # region ######################## Facial Recognition Preloading and Monitoring
    def _start_preloading(self):
        """Start preloading facial recognition in background"""
        import threading
        
        self.fr_ready = False
        self.camera_ready = False
        
        def preload_worker():
            try:
                result = fr.preload_everything()
                
                # Handle different return values from preload_everything()
                if result == FaceRecognitionError.SUCCESS:
                    # Success - enable facial recognition
                    self.fr_ready = fr.preloading_complete
                    self.camera_ready = fr.camera_ready
                    
                    # Update UI on main thread - enable button when facial recognition is ready
                    if self.fr_ready:
                        def enable_ui():
                            try:
                                if hasattr(self, 'log_scan_btn'):
                                    self.log_scan_btn.configure(text="Log Item Use", state="normal")
                                if hasattr(self, 'personal_db_btn'):
                                    self.personal_db_btn.configure(text="View Personal Database", state="normal")
                                self.set_status_indicator("#22c55e", "log_scan_indicator")
                                self.set_status_indicator("#22c55e", "personal_db_indicator")
                            except Exception as e:
                                print(f"Error enabling UI: {e}")
                        self.after(0, enable_ui)
                    else:
                        def disable_ui():
                            try:
                                if hasattr(self, 'log_scan_btn'):
                                    self.log_scan_btn.configure(text="Log Item Use", state="disabled")
                                if hasattr(self, 'personal_db_btn'):
                                    self.personal_db_btn.configure(text="View Personal Database", state="disabled")
                                self.set_status_indicator("#94a3b8", "log_scan_indicator")
                                self.set_status_indicator("#94a3b8", "personal_db_indicator")
                            except Exception as e:
                                print(f"Error disabling UI: {e}")
                        self.after(0, disable_ui)
                else:
                    # Error occurred - show appropriate error message
                    self.fr_ready = False
                    self.camera_ready = False
                    
                    # Map error codes to user-friendly messages
                    error_messages = {
                        FaceRecognitionError.REFERENCE_FOLDER_ERROR: "Reference folder not found. Please add reference images to assets/references/",
                        FaceRecognitionError.MODEL_LOAD_FAILED: "Failed to load face recognition model. Please check dependencies.",
                        FaceRecognitionError.PRELOAD_FAILED: "Failed to initialize facial recognition system.",
                        FaceRecognitionError.CAMERA_ERROR: "Camera not found or could not be initialized.",
                    }
                    
                    error_msg = error_messages.get(result, f"Initialization failed: {result.message}")
                    
                    def show_error():
                        try:
                            self.show_popup("Initialization Error", error_msg, "error")
                            self.log_scan_btn.configure(text="Log Item Use", state="disabled")
                        except Exception as ui_error:
                            print(f"Failed to show error dialog: {ui_error}")
                    self.after(500, show_error)
            except Exception as e:
                print(f"Preloading error: {e}")
                # Show error in UI - ensure proper thread scheduling with longer delay
                error_msg = f"Failed to initialize facial recognition system:\n{str(e)}"
                def show_error():
                    try:
                        self.show_popup("Initialization Error", error_msg, "error")
                        self.log_scan_btn.configure(text="Log Item Use", state="disabled")
                    except Exception as ui_error:
                        print(f"Failed to show error dialog: {ui_error}")
                        # Try again with longer delay
                        self.after(1000, lambda: self.show_popup("Initialization Error", error_msg, "error"))
                self.after(500, show_error)  # Longer delay to ensure UI is ready
        
        thread = threading.Thread(target=preload_worker, daemon=True)
        thread.start()

    def _start_camera_recovery_monitor(self):
        """Monitor camera status and attempt recovery if disconnected"""
        import threading
        import time
        
        def camera_monitor():
            """Continuously check if camera can be recovered with exponential backoff"""
            check_interval = 5  # Start checking every 5 seconds
            max_interval = 120  # Cap at 2 minutes
            
            while True:
                try:
                    # If camera is not ready and facial recognition is loaded, try recovery
                    if not self.camera_ready and self.fr_ready:
                        if fr.reinitialize_camera():
                            self.camera_ready = True
                            fr.camera_ready = True
                            check_interval = 5  # Reset to fast checking on success
                            # Update UI on main thread with stronger update
                            def update_ui():
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
                            
                            self.after(0, update_ui)
                        else:
                            # Increase check interval on failure (exponential backoff)
                            check_interval = min(check_interval * 1.5, max_interval)
                    else:
                        # Camera is ready, reset to normal checking
                        check_interval = 5
                    
                    time.sleep(check_interval)
                    
                except Exception as e:
                    print(f"Camera monitor error: {e}")
                    check_interval = min(check_interval * 2, max_interval)
                    time.sleep(check_interval)
        
        monitor_thread = threading.Thread(target=camera_monitor, daemon=True)
        monitor_thread.start()

    def set_status_indicator(self, color, indicator_name="log_scan_indicator"):
        """Update a status indicator color by name
        
        Args:
            color: hex color string (e.g., "#22c55e")
            indicator_name: name of the indicator attribute (default: "log_scan_indicator")
        """
        try:
            if hasattr(self, indicator_name):
                getattr(self, indicator_name).configure(fg_color=color)
                getattr(self, indicator_name).update()  # Force immediate update
        except Exception as e:
            # Silently ignore if status_indicator doesn't exist
            pass

    def face_recognition_with_timeout(self, btn, btn_text):
        """Run face recognition with timeout and visual feedback"""
        import threading
        import time
        
        # Determine which indicator to use based on button name
        indicator_name = "log_scan_indicator" if btn == "log_scan_btn" else "personal_db_indicator"
        
        # Set status to scanning (amber/yellow)
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
    
        # Start recognition in background
        thread = threading.Thread(target=recognition_worker, daemon=True)
        thread.start()
        
        # Wait with timeout (5 seconds)
        timeout_seconds = 5
        start_time = time.time()
        
        while not result["completed"] and (time.time() - start_time) < timeout_seconds:
            self.update()
            time.sleep(0.1)
        
        # Reset button and status
        if hasattr(self, btn):
            getattr(self, btn).configure(state="normal", text=btn_text)
        
        if not result["completed"]:
            # Timeout occurred
            self.set_status_indicator("#dc2626", indicator_name)
            default_status = "#22c55e" if self.fr_ready else "#94a3b8"
            self.after(2000, lambda: self.set_status_indicator(default_status, indicator_name))
            return "timeout"
        else:
            # Completed normally - reset status to defaultmake face id work with the new ui,

            default_status = "#22c55e" if self.fr_ready else "#94a3b8"
            self.set_status_indicator(default_status, indicator_name)
            return result["value"]

    def process_face_recognition_result(self, btn, result= None):
        """Process face recognition result and return username"""
        
        # Determine which indicator to use based on button name
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
        
        # Handle old numeric error codes for backward compatibility
        if isinstance(result, int):
            if result == 4:
                self.show_popup("Camera Error", "Couldn't find camera", "error")
            elif result == 3:
                self.show_popup("Reference Folder Error", "No reference folder found", "error")
            elif result == 2:
                self.show_popup("No Faces Found", "No faces found in reference images", "error")
            return ""

        # expected: list/tuple of detected names (or empty list)
        if isinstance(result, (list, tuple)):
            if not result:
                self.show_popup("Face Recognition", "No known faces detected.", "info")
                return ""
            # use the first detected name as the user
            detected_name = str(result[0])
            self.show_popup("Face Recognition", f"Detected: {detected_name}", "info")
            return detected_name

        # unexpected return type
        self.show_popup("Face Recognition", f"Unexpected result from recognizer: {result}", "error")
        return ""
    #endregion
    
    # def face_recognition(self):
    #     # run face recognition and return a username (string) if available
    #     if self.fr_ready:
    #         result = fr.quick_detect()  # Ultra-fast version
    #     else:
    #         result = fr.main()  # Fallback

    #     return self.process_face_recognition_result(result)

    def scan_face(self, scan_text, btn, btn_text):
        """Perform face recognition with pre-checks and error handling\n
        scan_text: description of the scan action (e.g., "log item use")\n
        btn: button widget to update during scan\n
        btn_text: original button text to restore after scan\n
        Returns the recognized username (str) or None if failed.
        """
        
        if not self.fr_ready:
            self.show_popup("Please Wait", "System is still loading. Please wait and try again.", "info")
            return
        
        # If camera wasn't ready at startup, try to reinitialize it now
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

    
    def _prompt_for_barcode(self, prompt="Scan barcode and press Enter", title="Scan Barcode"):
        """
        Open a modal dialog with a single Entry focused. Return the scanned text
        (str) when Enter is pressed, or None if canceled/closed.
        Works with barcode scanners that act as keyboard input (they send Enter).
        """
        # Use CTkToplevel for a consistent modern dialog
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.transient(self)
        dlg.resizable(False, False)

        ctk.CTkLabel(dlg, text=prompt, anchor="w", font=("Arial", 22)).pack(padx=25, pady=(22, 12))

        entry_var = tk.StringVar()
        entry = ctk.CTkEntry(dlg, textvariable=entry_var, width=600, height=55, font=("Arial", 20))
        entry.pack(padx=25, pady=(0, 22))

        result = {"value": None}

        def on_ok(event=None):
            val = entry_var.get().strip()
            if val == "":
                # ignore empty submit
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

        # Buttons
        btn_frame = ctk.CTkFrame(dlg, corner_radius=6)
        btn_frame.pack(pady=(0, 22), padx=18, fill="x")
        ok_btn = ctk.CTkButton(btn_frame, text="OK", command=on_ok, width=160, height=55, font=("Arial", 20))
        ok_btn.pack(side="left", padx=12, pady=12)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=on_cancel, width=160, height=55, font=("Arial", 20), fg_color="gray30")
        cancel_btn.pack(side="left", padx=12, pady=12)

        # Bind Enter to OK and Escape to cancel
        entry.bind("<Return>", on_ok)
        dlg.bind("<Escape>", on_cancel)

        # Center dialog over parent
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (dlg.winfo_reqwidth() // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (dlg.winfo_reqheight() // 2)
        dlg.geometry(f"+{x}+{y}")
        
        # Delay grab_set and focus until window is viewable
        def do_grab():
            try:
                dlg.grab_set()
                entry.focus_set()
            except:
                pass
        dlg.after(50, do_grab)

        # Wait for user (modal)
        self.wait_window(dlg)
        return result["value"]

    def log_scan(self):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        """Wait for a barcode to be scanned (or typed) and log current date/time + barcode."""
        user = self.scan_face(scan_text="log item use", btn="log_scan_btn", btn_text="Log Item Use")
        if user is None or user == "":
            return
        
        barcode = self._prompt_for_barcode()
        if barcode is None:
            return

        try:
            # Add scan to database
            log = self.db.add_to_inventory(barcode, user)
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
        self.show_popup("Logged", f"Logged {barcode} at {time} by {user}", "info")

    def load_data(self):
        """Read from database and load rows into the table."""
        # Cache rows and populate via the filter function so UI filters/search work.
        try:
            rows = list(self.db.pull_data("drugs_in_inventory"))
        except Exception as e:
            print("Error reading database:", e)
            rows = []

        # Store raw DB rows for filtering; typical shape: (barcode, drug, est_amount, exp_date)
        self._all_rows = rows
        # Populate the tree according to current filters/search
        self.apply_search_filter()
    
    

    def admin(self, title, prompt="Enter admin code"):
        code = 1234
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.transient(self)
        dlg.resizable(False, False)

        # --- create widgets ---
        ctk.CTkLabel(dlg, text=prompt, font=("Arial", 22)).pack(padx=25, pady=(22,12))
        entry_var = tk.StringVar()
        entry = ctk.CTkEntry(dlg, textvariable=entry_var, width=400, height=55, font=("Arial", 20), show="*")
        entry.pack(padx=25, pady=(0,22))

        # --- numpad frame ---
        button_frame = ctk.CTkFrame(dlg)
        button_frame.pack(pady=(0,22))

        buttons = [
            ['7','8','9'],
            ['4','5','6'],
            ['1','2','3'],
            ['C','0','<']
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

        # --- OK / Cancel buttons ---
        result = {"value": None}
        btn_frame = ctk.CTkFrame(dlg)
        btn_frame.pack(pady=(0,22), fill="x")
        
        def on_ok(event=None):
            val = entry_var.get().strip()
            if val != "":
                result["value"] = val
                dlg.destroy()

        def on_cancel(event=None):
            dlg.destroy()

        ctk.CTkButton(btn_frame, text="OK", command=on_ok, width=160, height=55, font=("Arial", 20)).pack(side="left", padx=12)
        ctk.CTkButton(btn_frame, text="Cancel", command=on_cancel, width=160, height=55, font=("Arial", 20), fg_color="gray30").pack(side="right", padx=12)

        entry.bind("<Return>", on_ok)
        dlg.bind("<Escape>", on_cancel)

        # --- force window to draw before grabbing ---
        dlg.update_idletasks()
        
        # Center dialog (don't make it fullscreen)
        x = self.winfo_rootx() + (self.winfo_width()//2) - (dlg.winfo_reqwidth()//2)
        y = self.winfo_rooty() + (self.winfo_height()//2) - (dlg.winfo_reqheight()//2)
        dlg.geometry(f"+{x}+{y}")
        
        # Ensure dialog is on top and has focus
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
            self.show_error("Admin Access Denied", "Incorrect admin code.")
            return False
        return True
    
    def delete_selected(self):
        if not self.admin("Enter admin code to delete scans"):
            return
        sel = self.tree.selection()
        
        if not sel:
            self.show_popup("Delete", "No row selected.", "info")
            return

        # Get deletion reason
        reason = simpledialog.askstring("Delete", "Enter reason for deletion (required):")
        if reason is None:  # User clicked Cancel
            return
        if not reason.strip():  # Empty or whitespace only
            self.show_popup("Error", "A deletion reason is required.", "error")
            return

        if not self.show_confirm("Confirm Delete", f"Delete {len(sel)} selected row(s)?\nReason: {reason}"):
            return

        try:
            admin_user = "ADMIN"
            for item_id in sel:
                values = self.tree.item(item_id)["values"]
                # Barcode is now the second column in the Treeview (index 1)
                barcode_value = values[1] if len(values) > 1 else values[0]
                self.db.delete_entry(barcode=barcode_value, reason=reason)
        except Exception as e:
            self.show_popup("Error", f"Failed to delete from database:\n{e}", "error")
            return

        self.load_data()
        self.show_popup("Deleted", f"Deleted {len(sel)} row(s).", "info")

    def show_history(self):

        """Show deletion history in a new window."""
        if not self.admin("View History"):
            return

        history = ctk.CTkToplevel(self)
        history.title("History")
        
        # Update idletasks to ensure window is ready
        history.update_idletasks()
        
        # Get screen dimensions
        screen_width = history.winfo_screenwidth()
        screen_height = history.winfo_screenheight()
        
        # Try fullscreen first, with robust fallback
        try:
            history.attributes("-fullscreen", True)
        except Exception:
            # Fallback: explicitly set geometry to screen size
            history.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Make window modal and ensure it gets focus
        try:
            history.transient(self)
            history.lift()
            history.focus_force()
            
            # Delay grab_set slightly to ensure window is visible
            def do_grab():
                try:
                    history.grab_set()
                except Exception as e:
                    print(f"Could not grab focus: {e}")
            history.after(100, do_grab)
        except Exception as e:
            print(f"Could not make history window modal: {e}")
       
        # NEW: top bar with close button
        top_bar = ctk.CTkFrame(history, corner_radius=6)
        top_bar.pack(fill="x", padx=18, pady=(18,0))
        ctk.CTkButton(top_bar, text="Close", command=history.destroy, width=160, height=55, font=("Arial", 22)).pack(side="right", padx=18, pady=18)
        history.bind("<Escape>", lambda e: history.destroy())

        # Create treeview for history
        columns = ("barcode", "name_of_item", "amount_changed", "user", "type", "time", "reason")
        tree = ttk.Treeview(history, columns=columns, show="headings")
        
        # Configure columns
        tree.heading("barcode", text="Barcode")
        tree.heading("name_of_item", text="Name of Item")
        tree.heading("amount_changed", text="Amount Changed")
        tree.heading("type", text="Type of Change")
        tree.heading("time", text="Time of Change")
        tree.heading("reason", text="Reason")
        tree.heading("user", text="User")

        # Add scrollbar
        scroll = ttk.Scrollbar(history, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        
        # Pack widgets
        tree.pack(side="left", fill="both", expand=True, padx=(18,0), pady=18)
        scroll.pack(side="right", fill="y", padx=(0,18), pady=18)

        # Load history data
        for row in self.db.pull_data("drug_changes"):
            tree.insert("", "end", values=row)


    def refresh_data(self):
        """Reload file periodically."""
        self.load_data()
        self.after(REFRESH_INTERVAL, self.refresh_data)

    def show_error(self, title="Error", message="An error occurred."):
        """Display an error window with the given title and message."""
        self.show_popup(title, message, "error")

    def _on_tree_click(self, event):
        """
        Toggle selection of the clicked row so multiple items can be selected
        by clicking them one-by-one (no Ctrl/Shift needed).
        Return "break" to suppress the default single-select behavior.
        """
        # Identify where the click occurred
        region = self.tree.identify_region(event.x, event.y)
        # Allow header/resize interactions to pass through to default handlers
        if region not in ("cell", "tree"):
            return None

        row = self.tree.identify_row(event.y)
        if not row:
            # Clicked empty area -> clear selection
            try:
                self.tree.selection_remove(self.tree.selection())
            except Exception:
                pass
            return "break"

        cur = list(self.tree.selection())
        if row in cur:
            # Deselect the clicked row
            cur.remove(row)
            self.tree.selection_set(tuple(cur))
        else:
            # Add clicked row to current selection
            cur.append(row)
            self.tree.selection_set(tuple(cur))

        # Prevent default handling which would reset selection to a single item
        return "break"

    def _on_tree_configure(self, event):
        """Handler for tree resize events: schedule adjusting visible column widths."""
        try:
            visible = [col for col, var in self.column_visibility.items() if var.get()]
            # Debounce: cancel any pending width adjustment before scheduling a new one
            try:
                if hasattr(self, "_column_adjust_after_id"):
                    self.after_cancel(self._column_adjust_after_id)
            except Exception:
                # If cancellation fails (e.g., ID already executed), ignore
                pass
            # schedule adjustment to avoid layout churn during configure bubbling
            # Only adjust if tree is actually visible and has width
            if self.tree.winfo_width() > 1:
                self._column_adjust_after_id = self.after(
                    100, lambda: self._adjust_column_widths(visible)
                )
        except Exception:
            # Intentionally ignore resize-related errors to prevent UI crashes
            pass

    def _adjust_column_widths(self, visible_columns):
        """Distribute available tree width across visible columns proportionally."""
        try:
            if not visible_columns:
                return
            
            # Ensure widget is ready
            if not self.tree.winfo_exists():
                return
                
            self.tree.update_idletasks()
            total_width = self.tree.winfo_width()
            
            if total_width <= 10:
                # fallback to parent width if tree not yet mapped
                try:
                    total_width = self.tree.master.winfo_width()
                except Exception:
                    total_width = sum(self.column_configs[c]["width"] for c in visible_columns) or 600
            
            # Don't adjust if width is still too small (not ready yet)
            if total_width < 100:
                return

            # Reserve small space for vertical scrollbar if present
            scrollbar_reserve = 18
            usable = max(100, total_width - scrollbar_reserve)

            # Use configured widths as minima / weights
            min_widths = [self.column_configs.get(c, {}).get("width", 100) for c in visible_columns]
            sum_min = sum(min_widths) if min_widths else 1

            # Distribute usable width proportionally across all columns, ensuring:
            # - widths are non-negative
            # - total width matches `usable`
            # - proportions follow min_widths as weights
            raw_widths = [usable * (wmin / sum_min) for wmin in min_widths]
            widths = [int(w) for w in raw_widths]
            current_total = sum(widths)
            diff = usable - current_total

            # Adjust for rounding so that sum(widths) == usable
            i = 0
            n = len(widths)
            while diff != 0 and n > 0:
                idx = i % n
                if diff > 0:
                    widths[idx] += 1
                    diff -= 1
                else:
                    # Avoid negative widths when reducing
                    if widths[idx] > 0:
                        widths[idx] -= 1
                        diff += 1
                i += 1

            for col, w in zip(visible_columns, widths):
                try:
                    self.tree.column(col, width=w, stretch=True)
                except Exception:
                    pass
        except Exception as e:
            # avoid crashing UI - silently ignore during startup
            pass  # Don't print errors during initialization
 
    def update_column_visibility(self):
        """Update which columns are displayed in the treeview based on checkbox states."""
        # Get list of visible columns
        visible_columns = [col for col, var in self.column_visibility.items() if var.get()]
        
        # Update the displaycolumns property
        if visible_columns:
            self.tree.configure(displaycolumns=visible_columns)
            # adjust widths after visibility change
            self.after(50, lambda: self._adjust_column_widths(visible_columns))
        else:
            # If no columns selected, show at least the drug column
            self.column_visibility["drug"].set(True)
            self.tree.configure(displaycolumns=["drug"])
            self.after(50, lambda: self._adjust_column_widths(["drug"]))

if __name__=="__main__":
    app = BarcodeViewer()
    app.mainloop()