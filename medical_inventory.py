import tkinter as tk
from tkinter import ttk
import csv
import os

LOG_FILE = "scans.csv"  # path to your file
REFRESH_INTERVAL = 3000  # 3 sec

class BarcodeViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Barcode Scan Log Viewer")
        self.geometry("700x400")

        # Title
        ttk.Label(self, text="medical inventory", font=("Arial", 16, "bold")).pack(pady=10)

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

    def load_data(self):
        """Read the CSV file and load rows into the table."""
        self.tree.delete(*self.tree.get_children())  # clear old data

        if not os.path.exists(LOG_FILE):
            print(f"File not found: {LOG_FILE}")
            return

        try:
            with open(LOG_FILE, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)  # skip header
                for row in reader:
                    if len(row) >= 2:
                        self.tree.insert("", "end", values=row)
        except Exception as e:
            print("Error reading file:", e)

    def refresh_data(self):
        """Reload file periodically."""
        self.load_data()
        self.after(REFRESH_INTERVAL, self.refresh_data)

if __name__ == "__main__":
    app = BarcodeViewer()
    app.mainloop()
