import sqlite3
from datetime import datetime

time_format = "%Y-%m-%d %H:%M:%S"

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Create the database and scans table if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    barcode TEXT NOT NULL,
                    user TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS deletion_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deleted_at TEXT NOT NULL,
                    deleted_by TEXT NOT NULL,
                    original_timestamp TEXT NOT NULL,
                    original_barcode TEXT NOT NULL,
                    original_user TEXT,
                    reason TEXT
                )
            ''')
            conn.commit()

    def _get_connection(self):
        """Helper method for tests to check database structure."""
        return sqlite3.connect(self.db_path)

    def add_scan(self, barcode, user):
        """Add a new scan to the database."""
        timestamp = datetime.now().strftime(time_format)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO scans (timestamp, barcode, user) VALUES (?, ?, ?)",
                (timestamp, barcode, user)
            )
            conn.commit()
        return timestamp

    def get_all_scans(self):
        """Return all scans as a list of tuples (timestamp, barcode, user)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT timestamp, barcode, user FROM scans ORDER BY timestamp DESC")
            return cursor.fetchall()

    def delete_scan(self, timestamp, barcode, user, deleted_by, reason=""):
        """Delete a scan and record who deleted it."""
        with sqlite3.connect(self.db_path) as conn:
            # Record deletion in history
            deleted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                """INSERT INTO deletion_history 
                   (deleted_at, deleted_by, original_timestamp, 
                    original_barcode, original_user, reason)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (deleted_at, deleted_by, timestamp, barcode, user, reason)
            )
            # Delete the scan
            conn.execute(
                "DELETE FROM scans WHERE timestamp=? AND barcode=? AND user=?",
                (timestamp, barcode, user)
            )
            conn.commit()

    def get_deletion_history(self):
        """Get all deletion records."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT deleted_at, deleted_by, original_timestamp,
                       original_barcode, original_user, reason
                FROM deletion_history
                ORDER BY deleted_at DESC
            """)
            return cursor.fetchall()
