import os
import pytest
from datetime import datetime
from db_manager import DatabaseManager

@pytest.fixture
def db():
    """Provide a fresh test database for each test."""
    test_db = "test_inventory.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    db = DatabaseManager(test_db)
    yield db
    if os.path.exists(test_db):
        os.remove(test_db)

def test_init_db_creates_tables(db):
    # Tables should exist after init
    with db._get_connection() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "scans" in table_names
        assert "deletion_history" in table_names

def test_add_and_get_scan(db):
    ts = db.add_scan("TEST123", "tester")
    assert isinstance(ts, str)
    scans = db.get_all_scans()
    assert len(scans) == 1
    assert scans[0][1] == "TEST123"
    assert scans[0][2] == "tester"

def test_delete_scan_creates_history(db):
    # Add and then delete a scan
    ts = db.add_scan("DEL123", "tester")
    db.delete_scan(ts, "DEL123", "tester", "admin", "test deletion")
    
    # Scan should be gone
    assert len(db.get_all_scans()) == 0
    
    # History should have one record
    history = db.get_deletion_history()
    assert len(history) == 1
    assert history[0][3] == "DEL123"  # original_barcode
    assert history[0][1] == "admin"    # deleted_by
    assert history[0][5] == "test deletion"  # reason
