#############################################
#to do list
#1. integrate facial recognition with barcode scanner
#2. fix bug where app crashes if you try to move the app with the camra open
#3. add feature to delete a row from the csv file
#4. add feature to edit a row from the csv file
#5. add feature to search for a specific barcode
#6. add feature to filter by date
#7. add feature to export the csv file
#8. add feature to convert barcode to text
#9. add voice recognition placeholder
#############################################



import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import csv
import os
import facial_recognition as fr
from datetime import datetime


# ensure scans.csv lives next to this script
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scans.csv")
REFRESH_INTERVAL = 3000  # 3 sec

class BarcodeViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Medical Inventory System")
        self.geometry("700x400")

        # keep current log path on the instance
        self.log_file = LOG_FILE

        # Title
        ttk.Label(self, text="Medical Inventory system" , font=("Arial", 16, "bold")).pack(pady=10)

        # Button frame (webcam + log + quit)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Open Camera", command=self.face_recognition).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Log Scan", command=self.log_scan).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Quit", command=self.destroy).grid(row=0, column=2, padx=5)

        # Create Treeview (table)
        columns = ("timestamp", "barcode")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("barcode", text="Barcode")

        # Add scrollbar
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(fill="both", expand=True, side="left", padx=(10, 0))
        scroll.pack(fill="y", side="right", padx=(0, 10))

        # Load data and start auto-refresh
        self.load_data()
        self.after(REFRESH_INTERVAL, self.refresh_data)

    def face_recognition(self):
        # open camera (test_cam.main is non-blocking if you pass a stop_event)
        fr.main()

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
        barcode = self._prompt_for_barcode()
        if barcode is None:
            # user cancelled or closed dialog
            return

        # ensure directory exists (ignore if dirname is empty)
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        except Exception:
            pass

        file_exists = os.path.exists(self.log_file)
        try:
            with open(self.log_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["timestamp", "barcode"])
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([ts, barcode])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write to CSV:\n{e}")
            return

        # reload view and notify user
        self.load_data()
        messagebox.showinfo("Logged", f"Logged {barcode} at {ts}")

    def load_data(self):
        """Read the CSV file and load rows into the table."""
        self.tree.delete(*self.tree.get_children())  # clear old data
        if not os.path.exists(self.log_file):
            print(f"File not found: {self.log_file}")
            return

        try:
            with open(self.log_file, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)  # skip header
                for row in reader:
                    if len(row) >= 2:
                        self.tree.insert("", "end", values=row)
        except Exception as e:
            print("Error reading file:", e)

    def file_path(self):
        # show which file we're reading (useful for debugging)
        print ("Looking for CSV at:", os.path.abspath(self.log_file))

        # Check if file exists
   

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
