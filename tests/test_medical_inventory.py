import os
import sys
import pytest
from tkinter import messagebox

# Add parent directory to path to import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.medical_inventory import BarcodeViewer
from src.db_manager import DatabaseManager

@pytest.fixture
def app(tmpdir):
    """Provide a test app instance using a temporary database."""
    app = BarcodeViewer()
    app.db = DatabaseManager(str(tmpdir / "test.db"))
    yield app
    app.destroy()

def test_app_init(app):
    """Test basic app initialization."""
    assert app.title() == "Medical Inventory System"
    assert app.tree.heading("barcode")["text"] == "Barcode"

def test_log_scan_requires_face_recognition(monkeypatch, app):
    """Test that scanning requires face recognition."""
    # Mock face recognition
    app.face_recognition = lambda: ""
    # Mock messagebox to capture error
    called = {"error": False}
    def mock_error(*args, **kwargs):
        called["error"] = True
    monkeypatch.setattr(messagebox, "showerror", mock_error)
    
    app.log_scan()
    assert called["error"]

def test_delete_requires_admin(app):
    """Test that deletion requires admin code."""
    app.admin = lambda x: False
    result = app.delete_selected()
    assert result is None

def test_show_deletion_history_requires_admin(app):
    """Test that viewing history requires admin code."""
    app.admin = lambda x: False
    result = app.show_deletion_history()
    assert result is None
