import tkinter as tk
from tkinter import ttk, messagebox
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
REFRESH_INTERVAL = 300000  # milliseconds
# Use CustomTkinter main window for modern look
ctk.set_appearance_mode("System")         # "Dark", "Light", or "System"
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
        style.configure("TLabel", font=("Arial", 20))
        style.configure("TButton", font=("Arial", 16), padding=10)
        style.configure("Treeview", font=("Arial", 15), rowheight=36)
        style.configure("Treeview.Heading", font=("Arial", 17, "bold"))

        # allow toggling fullscreen with F11 and exit fullscreen with Escape
        self.bind("<F11>", lambda e: self.attributes("-fullscreen", not self.attributes("-fullscreen")))
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))

        # keep current log path on the instance
        # self.log_file = LOG_FILE

        # Title (use CTkLabel for modern appearance)
        ctk.CTkLabel(self, text="Medical Inventory System", font=("Arial", 22, "bold")).pack(pady=12)

        # Main frame containing sidebar (left) and content (right)
        main_frame = ctk.CTkFrame(self, corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=8, pady=(4,12))

        # Sidebar on the left with buttons, search and filters
        sidebar = ctk.CTkFrame(main_frame, width=260, corner_radius=8)
        sidebar.pack(side="left", fill="y", padx=(8,12), pady=8)

        # Search placeholder
        ctk.CTkLabel(sidebar, text="Search", anchor="w").pack(padx=12, pady=(12,4), fill="x")
        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(sidebar, textvariable=self.search_var, placeholder_text="Search by barcode or drug...", width=220)
        search_entry.pack(padx=12, pady=(0,8))
        search_entry.bind("<KeyRelease>", self.apply_search_filter)

        # Filter placeholder
        ctk.CTkLabel(sidebar, text="Filters", anchor="w").pack(padx=12, pady=(8,4), fill="x")

        self.filter_var = tk.StringVar(value="All")
        filter_opts = ["All", "Expiring Soon", "Expired"]
        ctk.CTkOptionMenu(sidebar, values=filter_opts, variable=self.filter_var, width=220, command=lambda v: self.apply_search_filter()).pack(padx=12, pady=(0,8))

        # Example checkbox placeholder (e.g., show only low stock)
        self.low_stock_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(sidebar, text="Show low stock only", variable=self.low_stock_var, command=self.apply_search_filter).pack(padx=12, pady=(4,8))

# Vertical button group in sidebar
        btns_frame = ctk.CTkFrame(sidebar, corner_radius=6)
        btns_frame.pack(padx=12, pady=(12,12), fill="x")

# Container to hold button + overlay indicator
        btn_container = ctk.CTkFrame(btns_frame, corner_radius=0, fg_color="transparent")
        btn_container.pack(pady=(6, 6))

        # Log Scan button (exact width 200px)
        self.log_scan_btn = ctk.CTkButton(
                btn_container,
                text="Log Scan",
                command=self.log_scan,
                width=200
        )
        self.log_scan_btn.pack()

        # CLEAN status indicator (no square, no border, no background)
        self.status_indicator = ctk.CTkFrame(
                btn_container,
                width=12,
                height=12,
                corner_radius=8,
                fg_color="#94a3b8",        # circle color
                bg_color="#1f538d",
        )
        self.status_indicator.pack_propagate(False)

        # Place it over the right edge of the button
        self.status_indicator.place(relx=1.0, rely=0.5, anchor="e", x=-8)

        # Change indicator color on button hover
        def on_enter(_):
            self.status_indicator.configure(bg_color="#14375e")
        def on_leave(_):
            self.status_indicator.configure(bg_color="#1f538d")

        self.log_scan_btn.bind("<Enter>", on_enter)
        self.log_scan_btn.bind("<Leave>", on_leave)

        # Make sure it renders above the button
        self.status_indicator.tkraise()

        
        ctk.CTkButton(btns_frame, text="Delete Selected", command=self.delete_selected, width=200).pack(pady=6)
        ctk.CTkButton(btns_frame, text="View History", command=self.show_history, width=200).pack(pady=6)
        ctk.CTkButton(btns_frame, text="Quit", command=self.destroy, width=200, fg_color="#b22222").pack(pady=6)

        # Content frame (right) for the treeview / main table
        content_frame = ctk.CTkFrame(main_frame, corner_radius=6)
        content_frame.pack(side="left", fill="both", expand=True, padx=(0,8), pady=8)

        # Create Treeview (table) with user column inside content frame
        columns = ("drug", "barcode", "est_amount", "exp_date")
        # keep extended selectmode but we intercept clicks to allow toggle-without-ctrl
        self.tree = ttk.Treeview(content_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("drug", text="Drug")
        self.tree.heading("barcode", text="Barcode")
        self.tree.heading("est_amount", text="Estimated Amount")
        self.tree.heading("exp_date", text="Expiration")

        # Bind left-click to toggle selection on rows without requiring Ctrl/Shift
        # Clicking on a row toggles it in the selection set; clicking empty area clears selection.
        self.tree.bind("<Button-1>", self._on_tree_click)

        # Add scrollbar (ttk scrollbar looks fine beside CTk styled widgets)
        scroll = ttk.Scrollbar(content_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(fill="both", expand=True, side="left", padx=(10, 0), pady=(8,12))
        scroll.pack(fill="y", side="right", padx=(0, 10), pady=(8,12))

        # Load data and start auto-refresh
        self.load_data()
        self.after(REFRESH_INTERVAL, self.refresh_data)
    
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
                                    self.log_scan_btn.configure(text="Log Scan", state="normal")
                                self.set_status_indicator("#22c55e")
                            except Exception as e:
                                print(f"Error enabling UI: {e}")
                        self.after(0, enable_ui)
                    else:
                        def disable_ui():
                            try:
                                if hasattr(self, 'log_scan_btn'):
                                    self.log_scan_btn.configure(text="Log Scan", state="disabled")
                                self.set_status_indicator("#94a3b8")
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
                            messagebox.showerror("Initialization Error", error_msg)
                            self.log_scan_btn.configure(text="Log Scan", state="disabled")
                        except Exception as ui_error:
                            print(f"Failed to show error dialog: {ui_error}")
                    self.after(500, show_error)
            except Exception as e:
                print(f"Preloading error: {e}")
                # Show error in UI - ensure proper thread scheduling with longer delay
                error_msg = f"Failed to initialize facial recognition system:\n{str(e)}"
                def show_error():
                    try:
                        messagebox.showerror("Initialization Error", error_msg)
                        self.log_scan_btn.configure(text="Log Scan", state="disabled")
                    except Exception as ui_error:
                        print(f"Failed to show error dialog: {ui_error}")
                        # Try again with longer delay
                        self.after(1000, lambda: messagebox.showerror("Initialization Error", error_msg))
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
                                    self.set_status_indicator("#22c55e")
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

    def set_status_indicator(self, color):
        """Update the status indicator color - the colored dot to the right of Log Scan button"""
        try:
            if hasattr(self, 'status_indicator'):
                self.status_indicator.configure(fg_color=color)
                self.status_indicator.update()  # Force immediate update
        except Exception as e:
            # Silently ignore if status_indicator doesn't exist
            pass

    def face_recognition_with_timeout(self):
        """Run face recognition with timeout and visual feedback"""
        import threading
        import time
        
        # Set status to scanning (amber/yellow)
        self.set_status_indicator("#f59e0b")
        if hasattr(self, 'log_scan_btn'):
            self.log_scan_btn.configure(state="disabled", text="Scanning...")
        
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
        if hasattr(self, 'log_scan_btn'):
            self.log_scan_btn.configure(state="normal", text="Log Scan")
        
        if not result["completed"]:
            # Timeout occurred
            self.set_status_indicator("#dc2626")
            default_status = "#22c55e" if self.fr_ready else "#94a3b8"
            self.after(2000, lambda: self.set_status_indicator(default_status))
            return "timeout"
        else:
            # Completed normally - reset status to default
            default_status = "#22c55e" if self.fr_ready else "#94a3b8"
            self.set_status_indicator(default_status)
            return result["value"]

    def process_face_recognition_result(self, result):
        """Process face recognition result and return username"""
        
        # Handle FaceRecognitionError enum types
        if isinstance(result, FaceRecognitionError):
            if result == FaceRecognitionError.CAMERA_ERROR:
                messagebox.showerror("Camera Error", "Camera could not be initialized.")
                self.camera_ready = False
                self.set_status_indicator("#dc2626")
                if hasattr(self, 'log_scan_btn'):
                    self.log_scan_btn.configure(state="disabled")
            elif result == FaceRecognitionError.CAMERA_DISCONNECTED:
                messagebox.showerror("Camera Disconnected", "Camera was disconnected. Please reconnect and try again.")
                self.set_status_indicator("#dc2626")
                self.camera_ready = False
                # Attempt to reinitialize camera
                if fr.reinitialize_camera():
                    self.camera_ready = True
                    messagebox.showinfo("Camera Reconnected", "Camera has been reconnected!")
                    if hasattr(self, 'log_scan_btn'):
                        self.log_scan_btn.configure(state="normal")
                else:
                    if hasattr(self, 'log_scan_btn'):
                        self.log_scan_btn.configure(state="disabled")
            elif result == FaceRecognitionError.REFERENCE_FOLDER_ERROR:
                messagebox.showerror("Reference Folder Error", "Reference images folder not found. Please add face images to assets/references/")
            elif result == FaceRecognitionError.FRAME_CAPTURE_FAILED:
                messagebox.showerror("Frame Capture Error", "Failed to capture frame from camera.")
                self.camera_ready = False
            else:
                messagebox.showerror("Recognition Error", f"An error occurred: {result.message}")
            return ""
        
        # Handle old numeric error codes for backward compatibility
        if isinstance(result, int):
            if result == 4:
                messagebox.showerror("Camera Error", "Couldn't find camera")
            elif result == 3:
                messagebox.showerror("Reference Folder Error", "No reference folder found")
            elif result == 2:
                messagebox.showerror("No Faces Found", "No faces found in reference images")
            return ""

        # expected: list/tuple of detected names (or empty list)
        if isinstance(result, (list, tuple)):
            if not result:
                messagebox.showinfo("Face Recognition", "No known faces detected.")
                return ""
            # use the first detected name as the user
            detected_name = str(result[0])
            messagebox.showinfo("Face Recognition", f"Detected: {detected_name}")
            return detected_name

        # unexpected return type
        messagebox.showerror("Face Recognition", f"Unexpected result from recognizer: {result}")
        return ""

    def face_recognition(self):
        # run face recognition and return a username (string) if available
        if self.fr_ready:
            result = fr.quick_detect()  # Ultra-fast version
        else:
            result = fr.main()  # Fallback

        return self.process_face_recognition_result(result)

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
        dlg.grab_set()
        dlg.resizable(False, False)

        ctk.CTkLabel(dlg, text=prompt, anchor="w").pack(padx=12, pady=(10, 6))

        entry_var = tk.StringVar()
        entry = ctk.CTkEntry(dlg, textvariable=entry_var, width=420, height=30)
        entry.pack(padx=12, pady=(0, 10))
        entry.focus_set()

        result = {"value": None}

        def on_ok(event=None):
            val = entry_var.get().strip()
            if val == "":
                # ignore empty submit
                return
            result["value"] = val
            dlg.grab_release()
            dlg.destroy()

        def on_cancel(event=None):
            dlg.grab_release()
            dlg.destroy()

        # Buttons
        btn_frame = ctk.CTkFrame(dlg, corner_radius=6)
        btn_frame.pack(pady=(0, 10), padx=8, fill="x")
        ok_btn = ctk.CTkButton(btn_frame, text="OK", command=on_ok, width=100)
        ok_btn.pack(side="left", padx=6, pady=6)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=on_cancel, width=100, fg_color="gray30")
        cancel_btn.pack(side="left", padx=6, pady=6)

        # Bind Enter to OK and Escape to cancel
        entry.bind("<Return>", on_ok)
        dlg.bind("<Escape>", on_cancel)

        # Center dialog over parent
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (dlg.winfo_reqwidth() // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (dlg.winfo_reqheight() // 2)
        dlg.geometry(f"+{x}+{y}")

        # Wait for user (modal)
        self.wait_window(dlg)
        return result["value"]

    def log_scan(self):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        """Wait for a barcode to be scanned (or typed) and log current date/time + barcode."""
        if not self.fr_ready:
            messagebox.showinfo("Please Wait", "System is still loading. Please wait and try again.")
            return
        
        # If camera wasn't ready at startup, try to reinitialize it now
        if not self.camera_ready:
            print("Camera not ready, attempting to reinitialize...")
            if fr.reinitialize_camera():
                self.camera_ready = True
                fr.camera_ready = True
                print("Camera reinitialized successfully")
            else:
                messagebox.showerror("Camera Error", "Could not find camera. Please make sure camera is connected.")
                return
            
        user_result = self.face_recognition_with_timeout()
        
        if user_result == "timeout":
            messagebox.showerror(f"Timeout", "Face recognition timed out after 5 seconds. Please try again.")
            print("Face recognition timeout")
            return
        elif isinstance(user_result, str) and user_result.startswith("Error:"):
            messagebox.showerror("Error", f"Face recognition failed: {user_result}")
            return
        
        user = self.process_face_recognition_result(user_result)
        
        if not user:
            messagebox.showerror("Authentication Required", "Face recognition must be successful before scanning barcodes.")
            return
        
        barcode = self._prompt_for_barcode()
        if barcode is None:
            return

        try:
            # Add scan to database
            log = self.db.add_to_inventory(barcode, user)
            if log == LookupError:
                messagebox.showerror("Error", f"No drug found with barcode: {barcode}")
                return
            elif log == IndexError:
                messagebox.showerror("Error", f"Drug with barcode {barcode} is already in inventory.")
                return

        except Exception as e:
            messagebox.showerror("Error", f"Failed to write to database:\n{e}")
            return

        self.load_data()
        messagebox.showinfo("Logged", f"Logged {barcode} at {time} by {user}")

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
    
    def apply_search_filter(self, event=None):
        """
        Apply search and filter UI to the cached DB rows and populate the treeview.
        Filters available:
         - search text (matches drug or barcode)
         - filter_var: "All", "Expiring Soon", "Expired"
         - low_stock_var checkbox (threshold)
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

        for row in rows:
            # Normalize DB row into (barcode, drug, est_amount, exp_date)
            try:
                barcode, drug, est_amount, exp_date_raw = row[0], row[1], row[2], row[3]
            except Exception:
                # fallback: use positional mapping if shape differs
                vals = list(row)
                barcode = vals[0] if len(vals) > 0 else ""
                drug = vals[1] if len(vals) > 1 else ""
                est_amount = vals[2] if len(vals) > 2 else ""
                exp_date_raw = vals[3] if len(vals) > 3 else None

            # Search filter
            if q:
                if q not in str(drug).lower() and q not in str(barcode).lower():
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

            # Display order: (drug, barcode, est_amount, exp_date)
            display_row = (drug, barcode, est_amount, exp_date_raw)
            self.tree.insert("", "end", values=display_row)

    def admin(self, prompt="Enter admin code to delete scans"):
       code = 1234
       if simpledialog.askstring("Admin Access", prompt, show="*") != str(code):
            messagebox.showerror("Access Denied", "Incorrect admin code.")
            sel = self.tree.selection()
            self.tree.selection_remove(*sel)
            return False

       return True
    
    def delete_selected(self):
        if not self.admin("Enter admin code to delete scans"):
            return
        sel = self.tree.selection()
        
        if not sel:
            messagebox.showinfo("Delete", "No row selected.")
            return

        # Get deletion reason
        reason = simpledialog.askstring("Delete", "Enter reason for deletion (required):")
        if reason is None:  # User clicked Cancel
            return
        if not reason.strip():  # Empty or whitespace only
            messagebox.showerror("Error", "A deletion reason is required.")
            return

        if not messagebox.askyesno("Confirm Delete", f"Delete {len(sel)} selected row(s)?\nReason: {reason}"):
            return

        try:
            admin_user = "ADMIN"
            for item_id in sel:
                values = self.tree.item(item_id)["values"]
                # Barcode is now the second column in the Treeview (index 1)
                barcode_value = values[1] if len(values) > 1 else values[0]
                self.db.delete_entry(barcode=barcode_value, reason=reason)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete from database:\n{e}")
            return

        self.load_data()
        messagebox.showinfo("Deleted", f"Deleted {len(sel)} row(s).")

    def show_history(self):
        """Show deletion history in a new window."""
        if not self.admin("Enter admin code to view history"):
            return

        history = ctk.CTkToplevel(self)
        history.title("History")
        try:
            history.attributes("-fullscreen", True)
        except Exception:
            history.geometry("1024x600")

        # NEW: top bar with close button
        top_bar = ctk.CTkFrame(history, corner_radius=6)
        top_bar.pack(fill="x", padx=8, pady=(8,0))
        ctk.CTkButton(top_bar, text="Close", command=history.destroy, width=90).pack(side="right", padx=8, pady=8)
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
        tree.pack(side="left", fill="both", expand=True, padx=(8,0), pady=8)
        scroll.pack(side="right", fill="y", padx=(0,8), pady=8)

        # Load history data
        for row in self.db.pull_data("drug_changes"):
            tree.insert("", "end", values=row)


    def refresh_data(self):
        """Reload file periodically."""
        self.load_data()
        self.after(REFRESH_INTERVAL, self.refresh_data)

    def show_error(self, title="Error", message="An error occurred."):
        """Display an error window with the given title and message."""
        messagebox.showerror(title, message)

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


if __name__ == "__main__":
    app = BarcodeViewer()
    app.mainloop()