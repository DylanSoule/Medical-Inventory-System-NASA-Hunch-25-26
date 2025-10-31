#############################################
#to do list
#SWITCH TO DATABASE
#1. integrate facial recognition with barcode scanner
#4. add feature to edit a row from the csv file
#5. add feature to search for a specific barcode
#6. add feature to filter by date
#7. add feature to export the csv file
#8. add feature to convert barcode to text
#9. add voice recognition placeholder
#boot on start up
#############################################



import tkinter as tk
from tkinter import ttk, messagebox
import os
from tkinter import simpledialog
import facial_recognition as fr
from db_manager import DatabaseManager

# Database file path
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")
REFRESH_INTERVAL = 300000  # milliseconds
class BarcodeViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        # Initialize database
        self.db = DatabaseManager(DB_FILE)

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
        ttk.Label(self, text="Medical Inventory system" , font=("Arial", 22, "bold")).pack(pady=12)

        # Button frame (webcam + log + quit)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Open Camera", command=self.face_recognition).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Log Scan", command=self.log_scan).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="View History", command=self.show_deletion_history).grid(row=0, column=3, padx=5)
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

    def face_recognition(self):
        # run face recognition and return a username (string) if available
        result = fr.main()

        # backward-compatible numeric error codes
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
        user = self.face_recognition()
        
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

# Example usage:
# self.show_error("File Error", "Could not open CSV file.")

if __name__ == "__main__":
    app = BarcodeViewer()
    app.mainloop()