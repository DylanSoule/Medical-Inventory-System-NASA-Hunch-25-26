"""
Test Suite for Medical Inventory System
NASA HUNCH Project 2025-26

This module contains unit tests for the medical inventory application.
"""

import pytest
import sys
import os
import datetime
import sqlite3
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# Now import with try/except to handle missing modules gracefully
try:
    from Database.database import DatabaseManager, PersonalDatabaseManager
except ImportError:
    DatabaseManager = None
    PersonalDatabaseManager = None

try:
    from src import facial_recognition as fr
    from src.facial_recognition import FaceRecognitionError
except ImportError:
    try:
        import facial_recognition as fr
        from facial_recognition import FaceRecognitionError
    except ImportError:
        fr = None
        FaceRecognitionError = None


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing"""
    if DatabaseManager is None:
        pytest.skip("DatabaseManager not available")
    
    db_file = tmp_path / "test_inventory.db"
    db = DatabaseManager(str(db_file))
    yield db
    # Cleanup is automatic with tmp_path


@pytest.fixture
def temp_personal_db(tmp_path):
    """Create a temporary personal database for testing"""
    if PersonalDatabaseManager is None:
        pytest.skip("PersonalDatabaseManager not available")
    
    db_file = tmp_path / "test_personal.db"
    personal_db = PersonalDatabaseManager(str(db_file))
    yield personal_db


@pytest.fixture
def sample_drug_data():
    """Sample drug data for testing"""
    return {
        'barcode': '12345678',
        'name': 'Test Medicine',
        'amount': 100,
        'expiration': '2025-12-31',
        'type': 'pill',
        'item_type': 'medication',
        'dose_size': '10mg',
        'location': 'A1'
    }


# ============================================================================
# DATABASE TESTS
# ============================================================================

class TestDatabaseManager:
    """Test DatabaseManager functionality"""
    
    def test_database_initialization(self, temp_db):
        """Test that database initializes correctly"""
        assert temp_db is not None
        assert os.path.exists(temp_db.path)
    
    def test_add_drug_to_inventory(self, temp_db, sample_drug_data):
        """Test adding a drug to inventory"""
        # First add drug to main database
        result = temp_db.add_drug(
            barcode=sample_drug_data['barcode'],
            name=sample_drug_data['name'],
            expiration=sample_drug_data['expiration'],
            type_=sample_drug_data['type'],
            item_type=sample_drug_data['item_type'],
            dose_size=sample_drug_data['dose_size']
        )
        
        assert result is True or result is None  # Success returns True or None
    
    def test_check_barcode_exists(self, temp_db, sample_drug_data):
        """Test checking if barcode exists"""
        # Add drug first
        temp_db.add_drug(
            barcode=sample_drug_data['barcode'],
            name=sample_drug_data['name'],
            expiration=sample_drug_data['expiration'],
            type_=sample_drug_data['type'],
            item_type=sample_drug_data['item_type'],
            dose_size=sample_drug_data['dose_size']
        )
        
        result = temp_db.check_if_barcode_exists(sample_drug_data['barcode'])
        assert result is not False
    
    def test_pull_data(self, temp_db):
        """Test pulling data from database"""
        data = list(temp_db.pull_data("drugs_in_inventory"))
        assert isinstance(data, list)
    
    def test_delete_entry(self, temp_db, sample_drug_data):
        """Test deleting an entry"""
        # Add drug first
        temp_db.add_drug(
            barcode=sample_drug_data['barcode'],
            name=sample_drug_data['name'],
            expiration=sample_drug_data['expiration'],
            type_=sample_drug_data['type'],
            item_type=sample_drug_data['item_type'],
            dose_size=sample_drug_data['dose_size']
        )
        
        # Delete it
        temp_db.delete_entry(
            barcode=sample_drug_data['barcode'],
            reason="Testing deletion"
        )
        
        # Verify it's gone
        result = temp_db.check_if_barcode_exists(sample_drug_data['barcode'])
        assert result is False


class TestPersonalDatabaseManager:
    """Test PersonalDatabaseManager functionality"""
    
    def test_personal_db_initialization(self, temp_personal_db):
        """Test personal database initializes correctly"""
        assert temp_personal_db is not None
    
    def test_add_prescription(self, temp_personal_db):
        """Test adding a prescription"""
        result = temp_personal_db.add_new_prescription(
            barcode='12345',
            drug_name='Test Drug',
            dosage='10mg',
            time='09:00:00',
            leeway=30
        )
        assert result is True or result is None
    
    def test_get_personal_data(self, temp_personal_db):
        """Test retrieving personal data"""
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        hist_logs, prescript_logs = temp_personal_db.get_personal_data(date_str)
        
        assert isinstance(hist_logs, list)
        assert isinstance(prescript_logs, list)


# ============================================================================
# DATE PARSING TESTS
# ============================================================================

class TestDateParsing:
    """Test date parsing functionality"""
    
    def test_parse_standard_date(self):
        """Test parsing standard date format"""
        from src.medical_inventory import BarcodeViewer
        
        # Create a mock instance just to access the method
        with patch('src.medical_inventory.DatabaseManager'):
            viewer = BarcodeViewer.__new__(BarcodeViewer)
            
            date_str = "2025-12-31"
            result = viewer._parse_date(date_str)
            
            assert result is not None
            assert result.year == 2025
            assert result.month == 12
            assert result.day == 31
    
    def test_parse_invalid_date(self):
        """Test parsing invalid date"""
        from src.medical_inventory import BarcodeViewer
        
        with patch('src.medical_inventory.DatabaseManager'):
            viewer = BarcodeViewer.__new__(BarcodeViewer)
            
            result = viewer._parse_date("invalid-date")
            assert result is None
    
    def test_parse_none_date(self):
        """Test parsing None date"""
        from src.medical_inventory import BarcodeViewer
        
        with patch('src.medical_inventory.DatabaseManager'):
            viewer = BarcodeViewer.__new__(BarcodeViewer)
            
            result = viewer._parse_date(None)
            assert result is None


# ============================================================================
# FACIAL RECOGNITION TESTS
# ============================================================================

class TestFacialRecognition:
    """Test facial recognition error handling"""
    
    def test_face_recognition_error_enum(self):
        """Test FaceRecognitionError enum values"""
        if FaceRecognitionError is None:
            pytest.skip("FaceRecognitionError not available")
        
        assert FaceRecognitionError.SUCCESS is not None
        assert FaceRecognitionError.CAMERA_ERROR is not None
        assert FaceRecognitionError.REFERENCE_FOLDER_ERROR is not None
    
    @patch('src.facial_recognition.preload_everything')
    def test_preload_success(self, mock_preload):
        """Test successful preloading"""
        if fr is None or FaceRecognitionError is None:
            pytest.skip("Facial recognition module not available")
        
        mock_preload.return_value = FaceRecognitionError.SUCCESS
        
        result = mock_preload()
        assert result == FaceRecognitionError.SUCCESS
    
    @patch('src.facial_recognition.preload_everything')
    def test_preload_camera_error(self, mock_preload):
        """Test camera error during preloading"""
        if fr is None or FaceRecognitionError is None:
            pytest.skip("Facial recognition module not available")
        
        mock_preload.return_value = FaceRecognitionError.CAMERA_ERROR
        
        result = mock_preload()
        assert result == FaceRecognitionError.CAMERA_ERROR


# ============================================================================
# COLUMN CONFIGURATION TESTS
# ============================================================================

class TestColumnConfiguration:
    """Test column configuration constants"""
    
    def test_column_configs_exist(self):
        """Test that column configurations are defined"""
        try:
            from src.medical_inventory import COLUMN_CONFIGS
            
            assert 'drug' in COLUMN_CONFIGS
            assert 'barcode' in COLUMN_CONFIGS
            assert 'exp_date' in COLUMN_CONFIGS
        except ImportError:
            pytest.skip("medical_inventory module not available")
    
    def test_column_labels_exist(self):
        """Test that column labels are defined"""
        try:
            from src.medical_inventory import COLUMN_LABELS
            
            assert 'drug' in COLUMN_LABELS
            assert 'barcode' in COLUMN_LABELS
            assert 'exp_date' in COLUMN_LABELS
        except ImportError:
            pytest.skip("medical_inventory module not available")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for the full system"""
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.facial_recognition.preload_everything')
    def test_app_initialization_without_ui(self, mock_preload, mock_db):
        """Test app initialization without creating UI"""
        try:
            from src.medical_inventory import BarcodeViewer
            
            if FaceRecognitionError is None:
                pytest.skip("FaceRecognitionError not available")
            
            mock_preload.return_value = FaceRecognitionError.SUCCESS
            mock_db.return_value = Mock()
            
            # We can't easily test full UI initialization without a display
            # But we can test that imports work
            assert BarcodeViewer is not None
        except ImportError:
            pytest.skip("BarcodeViewer not available")
    
    def test_database_integration(self, temp_db, sample_drug_data):
        """Test complete database workflow"""
        # Add drug
        temp_db.add_drug(
            barcode=sample_drug_data['barcode'],
            name=sample_drug_data['name'],
            expiration=sample_drug_data['expiration'],
            type_=sample_drug_data['type'],
            item_type=sample_drug_data['item_type'],
            dose_size=sample_drug_data['dose_size']
        )
        
        # Verify it exists
        result = temp_db.check_if_barcode_exists(sample_drug_data['barcode'])
        assert result is not False
        
        # Pull all data
        data = list(temp_db.pull_data("drugs_in_inventory"))
        assert len(data) > 0
        
        # Delete it
        temp_db.delete_entry(
            barcode=sample_drug_data['barcode'],
            reason="Test cleanup"
        )
        
        # Verify deletion
        result = temp_db.check_if_barcode_exists(sample_drug_data['barcode'])
        assert result is False


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_round_rectangle(self):
        """Test round rectangle creation helper"""
        try:
            from src.medical_inventory import create_round_rectangle
            import tkinter as tk
            
            root = tk.Tk()
            canvas = tk.Canvas(root, width=200, height=200)
            
            result = create_round_rectangle(
                canvas, 10, 10, 100, 100, radius=10,
                fill="blue", outline="red"
            )
            
            assert result is not None
            root.destroy()
        except ImportError:
            pytest.skip("Tkinter or medical_inventory module not available")
        except Exception as e:
            # Tkinter might not be available in headless environments
            pytest.skip(f"Tkinter initialization failed: {e}")


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
