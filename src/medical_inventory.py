import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from tkinter import simpledialog

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import facial_recognition as fr
from facial_recognition import FaceRecognitionError
from db_manager import DatabaseManager

# Database file path - store in parent directory
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "inventory.db")
REFRESH_INTERVAL = 300000  # milliseconds
class BarcodeViewer(tk.Tk):
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
        style = ttk.Style(self)
        style.configure("TLabel", font=("Arial", 20))
        style.configure("TButton", font=("Arial", 16), padding=10)
        style.configure("Treeview", font=("Arial", 16), rowheight=36)
        style.configure("Treeview.Heading", font=("Arial", 18, "bold"))

        # allow toggling fullscreen with F11 and exit fullscreen with Escape
        self.bind("<F11>", lambda e: self.attributes("-fullscreen", not self.attributes("-fullscreen")))
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))

        # keep current log path on the instance
        # self.log_file = LOG_FILE

        # Title
        ttk.Label(self, text="Medical Inventory System" , font=("Arial", 22, "bold")).pack(pady=12)

        # Button frame (webcam + log + quit)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)
        
        # Log scan button with status indicator
        log_frame = ttk.Frame(btn_frame)
        log_frame.grid(row=0, column=1, padx=5)
        
        # Status canvas (small perfect circle)
        self.status_canvas = tk.Canvas(log_frame, width=16, height=16, highlightthickness=0)
        self.status_canvas.pack(side="left", padx=(0, 5))
        self.status_circle = self.status_canvas.create_oval(2, 2, 14, 14, fill="gray", outline="", width=0)
        
        self.log_scan_btn = ttk.Button(log_frame, text="Log Scan", command=self.log_scan, state="disabled")
        self.log_scan_btn.pack(side="left")
        
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="View Deletion History", command=self.show_deletion_history).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="Quit", command=self.destroy).grid(row=0, column=4, padx=5)

        # Create Treeview (table) with user column
        columns = ("timestamp", "barcode", "user")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("barcode", text="Barcode")
        self.tree.heading("user", text="User")

        # Add scrollbar
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(fill="both", expand=True, side="left", padx=(10, 0))
        scroll.pack(fill="y", side="right", padx=(0, 10))

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
                        self.after(0, lambda: [
                            self.log_scan_btn.configure(text="Log Scan", state="normal"),
                            self.set_status_indicator("#22c55e")
                        ])
                    else:
                        self.after(0, lambda: [
                            self.log_scan_btn.configure(text="Log Scan", state="disabled"),
                            self.set_status_indicator("#94a3b8")
                        ])
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
        """Update the status indicator color"""
        try:
            self.status_canvas.itemconfig(self.status_circle, fill=color)
            self.status_canvas.update()  # Force immediate update
        except Exception as e:
            print(f"Error updating status indicator: {e}")

    def face_recognition_with_timeout(self):
        """Run face recognition with timeout and visual feedback"""
        import threading
        import time
        
        # Set status to scanning (amber/yellow)
        self.set_status_indicator("#f59e0b")
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
                self.log_scan_btn.configure(state="disabled")
            elif result == FaceRecognitionError.CAMERA_DISCONNECTED:
                messagebox.showerror("Camera Disconnected", "Camera was disconnected. Please reconnect and try again.")
                self.set_status_indicator("#dc2626")
                self.camera_ready = False
                # Attempt to reinitialize camera
                if fr.reinitialize_camera():
                    self.camera_ready = True
                    messagebox.showinfo("Camera Reconnected", "Camera has been reconnected!")
                    self.log_scan_btn.configure(state="normal")
                else:
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
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        ttk.Label(dlg, text=prompt).pack(padx=12, pady=(8, 4))

        entry_var = tk.StringVar()
        entry = ttk.Entry(dlg, textvariable=entry_var, width=40)
        entry.pack(padx=12, pady=(0, 8))
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
        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(pady=(0, 8))
        ok_btn = ttk.Button(btn_frame, text="OK", command=on_ok)
        ok_btn.pack(side="left", padx=6)
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=on_cancel)
        cancel_btn.pack(side="left", padx=6)

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
            ts = self.db.add_scan(barcode, user)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write to database:\n{e}")
            return

        self.load_data()
        messagebox.showinfo("Logged", f"Logged {barcode} at {ts} by {user}")

    def load_data(self):
        """Read from database and load rows into the table."""
        self.tree.delete(*self.tree.get_children())
        
        try:
            rows = self.db.get_all_scans()
            for row in rows:
                self.tree.insert("", "end", values=row)
        except Exception as e:
            print("Error reading database:", e)
    
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

        if not messagebox.askyesno("Confirm Delete", 
            f"Delete {len(sel)} selected row(s)?\nReason: {reason}"):
            return

        try:
            admin_user = "ADMIN"
            for item_id in sel:
                values = self.tree.item(item_id)["values"]
                self.db.delete_scan(*values, deleted_by=admin_user, reason=reason.strip())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete from database:\n{e}")
            return

        self.load_data()
        messagebox.showinfo("Deleted", f"Deleted {len(sel)} row(s).")

    def show_deletion_history(self):
        """Show deletion history in a new window."""
        if not self.admin("Enter admin code to view history"):
            return

        history = tk.Toplevel(self)
        history.title("Deletion History")
        history.geometry("800x600")

        # Create treeview for history
        columns = ("deleted_at", "deleted_by", "original_timestamp", 
                  "original_barcode", "original_user", "reason")
        tree = ttk.Treeview(history, columns=columns, show="headings")
        
        # Configure columns
        tree.heading("deleted_at", text="Deleted At")
        tree.heading("deleted_by", text="Deleted By")
        tree.heading("original_timestamp", text="Original Time")
        tree.heading("original_barcode", text="Barcode")
        tree.heading("original_user", text="Original User")
        tree.heading("reason", text="Reason")

        # Add scrollbar
        scroll = ttk.Scrollbar(history, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        
        # Pack widgets
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Load history data
        for row in self.db.get_deletion_history():
            tree.insert("", "end", values=row)

        # Close button
        ttk.Button(history, text="Close", 
                  command=history.destroy).pack(pady=10)

    def refresh_data(self):
        """Reload file periodically."""
        self.load_data()
        self.after(REFRESH_INTERVAL, self.refresh_data)

    def show_error(self, title="Error", message="An error occurred."):
        """Display an error window with the given title and message."""
        messagebox.showerror(title, message)


if __name__ == "__main__":
    app = BarcodeViewer()
    app.mainloop()