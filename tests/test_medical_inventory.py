"""
Test Suite for Medical Inventory System
NASA HUNCH Project 2025-26

This module contains unit tests for the medical inventory application.
Tests focus on functionality that doesn't require UI rendering.
"""

import pytest
import sys
import os
import datetime
from unittest.mock import Mock, patch, MagicMock, PropertyMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# CONSTANTS TESTS
# ============================================================================

class TestConstants:
    """Test application constants"""
    
    def test_refresh_interval_defined(self):
        """Test that REFRESH_INTERVAL constant is defined"""
        from src.medical_inventory import REFRESH_INTERVAL
        
        assert REFRESH_INTERVAL is not None
        assert isinstance(REFRESH_INTERVAL, int)
        assert REFRESH_INTERVAL > 0
        assert REFRESH_INTERVAL == 30000
    
    def test_db_file_path_defined(self):
        """Test that DB_FILE path is defined"""
        from src.medical_inventory import DB_FILE
        
        assert DB_FILE is not None
        assert isinstance(DB_FILE, str)
        assert 'inventory.db' in DB_FILE


# ============================================================================
# COLUMN CONFIGURATION TESTS
# ============================================================================

class TestColumnConfiguration:
    """Test column configuration constants"""
    
    def test_column_configs_exist(self):
        """Test that column configurations are defined"""
        from src.medical_inventory import COLUMN_CONFIGS
        
        required_columns = ['drug', 'barcode', 'est_amount', 'exp_date', 'type_', 'dose_size', 'item_type', 'item_loc']
        
        for col in required_columns:
            assert col in COLUMN_CONFIGS, f"Missing column config: {col}"
    
    def test_column_labels_exist(self):
        """Test that column labels are defined"""
        from src.medical_inventory import COLUMN_LABELS
        
        required_columns = ['drug', 'barcode', 'est_amount', 'exp_date', 'type_', 'dose_size', 'item_type', 'item_loc']
        
        for col in required_columns:
            assert col in COLUMN_LABELS, f"Missing column label: {col}"
    
    def test_column_configs_have_required_fields(self):
        """Test that each column config has required fields"""
        from src.medical_inventory import COLUMN_CONFIGS
        
        for col_id, config in COLUMN_CONFIGS.items():
            assert 'text' in config, f"Column {col_id} missing 'text' field"
            assert 'width' in config, f"Column {col_id} missing 'width' field"
            assert isinstance(config['width'], int), f"Column {col_id} width should be int"
            assert config['width'] > 0, f"Column {col_id} width should be positive"
    
    def test_column_labels_match_configs(self):
        """Test that column labels match configuration keys"""
        from src.medical_inventory import COLUMN_CONFIGS, COLUMN_LABELS
        
        assert set(COLUMN_CONFIGS.keys()) == set(COLUMN_LABELS.keys()), \
            "Column configs and labels should have matching keys"


# ============================================================================
# DATE PARSING TESTS
# ============================================================================

class TestDateParsing:
    """Test date parsing functionality"""
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_parse_standard_date_format(self, mock_fr, mock_db):
        """Test parsing standard YYYY-MM-DD format"""
        from src.medical_inventory import BarcodeViewer
        
        with patch.object(BarcodeViewer, '__init__', lambda x: None):
            viewer = BarcodeViewer()
            
            result = viewer._parse_date("2025-12-31")
            
            assert result is not None
            assert isinstance(result, datetime.date)
            assert result.year == 2025
            assert result.month == 12
            assert result.day == 31
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_parse_slash_date_format(self, mock_fr, mock_db):
        """Test parsing YYYY/MM/DD format"""
        from src.medical_inventory import BarcodeViewer
        
        with patch.object(BarcodeViewer, '__init__', lambda x: None):
            viewer = BarcodeViewer()
            
            result = viewer._parse_date("2025/12/31")
            
            assert result is not None
            assert result.year == 2025
            assert result.month == 12
            assert result.day == 31
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_parse_us_date_format(self, mock_fr, mock_db):
        """Test parsing MM/DD/YYYY format"""
        from src.medical_inventory import BarcodeViewer
        
        with patch.object(BarcodeViewer, '__init__', lambda x: None):
            viewer = BarcodeViewer()
            
            result = viewer._parse_date("12/31/2025")
            
            assert result is not None
            assert result.year == 2025
            assert result.month == 12
            assert result.day == 31
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_parse_date_object(self, mock_fr, mock_db):
        """Test parsing existing date object"""
        from src.medical_inventory import BarcodeViewer
        
        with patch.object(BarcodeViewer, '__init__', lambda x: None):
            viewer = BarcodeViewer()
            
            input_date = datetime.date(2025, 12, 31)
            result = viewer._parse_date(input_date)
            
            assert result is not None
            assert result == input_date
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_parse_invalid_date(self, mock_fr, mock_db):
        """Test parsing invalid date string"""
        from src.medical_inventory import BarcodeViewer
        
        with patch.object(BarcodeViewer, '__init__', lambda x: None):
            viewer = BarcodeViewer()
            
            result = viewer._parse_date("invalid-date")
            assert result is None
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_parse_none_date(self, mock_fr, mock_db):
        """Test parsing None"""
        from src.medical_inventory import BarcodeViewer
        
        with patch.object(BarcodeViewer, '__init__', lambda x: None):
            viewer = BarcodeViewer()
            
            result = viewer._parse_date(None)
            assert result is None
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_parse_empty_string(self, mock_fr, mock_db):
        """Test parsing empty string"""
        from src.medical_inventory import BarcodeViewer
        
        with patch.object(BarcodeViewer, '__init__', lambda x: None):
            viewer = BarcodeViewer()
            
            result = viewer._parse_date("")
            assert result is None
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_parse_datetime_with_time(self, mock_fr, mock_db):
        """Test parsing datetime string with time component"""
        from src.medical_inventory import BarcodeViewer
        
        with patch.object(BarcodeViewer, '__init__', lambda x: None):
            viewer = BarcodeViewer()
            
            result = viewer._parse_date("2025-12-31 14:30:00")
            
            assert result is not None
            assert result.year == 2025
            assert result.month == 12
            assert result.day == 31


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_round_rectangle_exists(self):
        """Test that create_round_rectangle function exists"""
        from src.medical_inventory import create_round_rectangle
        
        assert callable(create_round_rectangle)
    
    def test_create_round_rectangle_parameters(self):
        """Test create_round_rectangle function signature"""
        from src.medical_inventory import create_round_rectangle
        import inspect
        
        sig = inspect.signature(create_round_rectangle)
        params = list(sig.parameters.keys())
        
        # Should have canvas, coordinates, radius, and kwargs
        assert 'canvas' in params
        assert 'x1' in params
        assert 'y1' in params
        assert 'x2' in params
        assert 'y2' in params
        assert 'radius' in params


# ============================================================================
# CLASS STRUCTURE TESTS
# ============================================================================

class TestBarcodeViewerClass:
    """Test BarcodeViewer class structure"""
    
    def test_barcode_viewer_class_exists(self):
        """Test that BarcodeViewer class exists"""
        from src.medical_inventory import BarcodeViewer
        
        assert BarcodeViewer is not None
        assert hasattr(BarcodeViewer, '__init__')
    
    def test_barcode_viewer_has_window_setup_methods(self):
        """Test that BarcodeViewer has window setup methods"""
        from src.medical_inventory import BarcodeViewer
        
        required_methods = [
            '_setup_window',
            '_setup_styles',
            '_setup_ui',
        ]
        
        for method_name in required_methods:
            assert hasattr(BarcodeViewer, method_name), f"Missing method: {method_name}"
    
    def test_barcode_viewer_has_data_methods(self):
        """Test that BarcodeViewer has data management methods"""
        from src.medical_inventory import BarcodeViewer
        
        required_methods = [
            'load_data',
            'refresh_data',
            'apply_search_filter',
            '_parse_date',
        ]
        
        for method_name in required_methods:
            assert hasattr(BarcodeViewer, method_name), f"Missing method: {method_name}"
    
    def test_barcode_viewer_has_ui_creation_methods(self):
        """Test that BarcodeViewer has UI creation methods"""
        from src.medical_inventory import BarcodeViewer
        
        required_methods = [
            '_create_sidebar',
            '_create_content_area',
            '_create_search_section_grid',
            '_create_filter_section_grid',
            '_create_column_visibility_section_grid',
            '_create_action_buttons_grid',
        ]
        
        for method_name in required_methods:
            assert hasattr(BarcodeViewer, method_name), f"Missing method: {method_name}"
    
    def test_barcode_viewer_has_user_action_methods(self):
        """Test that BarcodeViewer has user action methods"""
        from src.medical_inventory import BarcodeViewer
        
        required_methods = [
            'personal_run',
            'log_item_use',
            'log_scan',
            'use_item',
            'delete_selected',
            'show_history',
        ]
        
        for method_name in required_methods:
            assert hasattr(BarcodeViewer, method_name), f"Missing method: {method_name}"
    
    def test_barcode_viewer_has_dialog_methods(self):
        """Test that BarcodeViewer has dialog helper methods"""
        from src.medical_inventory import BarcodeViewer
        
        required_methods = [
            '_prompt_for_barcode',
            '_prompt_for_amount',
            'admin',
            'show_popup',
            'show_confirm',
            'show_error',
        ]
        
        for method_name in required_methods:
            assert hasattr(BarcodeViewer, method_name), f"Missing method: {method_name}"
    
    def test_barcode_viewer_has_treeview_methods(self):
        """Test that BarcodeViewer has treeview management methods"""
        from src.medical_inventory import BarcodeViewer
        
        required_methods = [
            'update_column_visibility',
            '_on_tree_click',
            '_on_tree_configure',
            '_adjust_column_widths',
        ]
        
        for method_name in required_methods:
            assert hasattr(BarcodeViewer, method_name), f"Missing method: {method_name}"
    
    def test_barcode_viewer_has_facial_recognition_methods(self):
        """Test that BarcodeViewer has facial recognition methods"""
        from src.medical_inventory import BarcodeViewer
        
        required_methods = [
            '_start_preloading',
            '_enable_facial_recognition_ui',
            '_disable_facial_recognition_ui',
            'scan_face',
            'set_status_indicator',
        ]
        
        for method_name in required_methods:
            assert hasattr(BarcodeViewer, method_name), f"Missing method: {method_name}"


class TestPersonalDbWindowClass:
    """Test Personal_db_window class structure"""
    
    def test_personal_db_window_class_exists(self):
        """Test that Personal_db_window class exists"""
        from src.medical_inventory import Personal_db_window
        
        assert Personal_db_window is not None
        assert hasattr(Personal_db_window, '__init__')
    
    def test_personal_db_window_has_timeline_methods(self):
        """Test that Personal_db_window has timeline methods"""
        from src.medical_inventory import Personal_db_window
        
        required_methods = [
            'load_timeline_data',
            'draw_timeline',
            '_draw_prescription_pill',
            '_draw_activity_pill',
            '_draw_legend',
        ]
        
        for method_name in required_methods:
            assert hasattr(Personal_db_window, method_name), f"Missing method: {method_name}"
    
    def test_personal_db_window_has_navigation_methods(self):
        """Test that Personal_db_window has navigation methods"""
        from src.medical_inventory import Personal_db_window
        
        required_methods = [
            'zoom_in',
            'zoom_out',
            'reset_zoom',
            'previous_day',
            'next_day',
            'goto_today',
        ]
        
        for method_name in required_methods:
            assert hasattr(Personal_db_window, method_name), f"Missing method: {method_name}"
    
    def test_personal_db_window_has_helper_methods(self):
        """Test that Personal_db_window has helper methods"""
        from src.medical_inventory import Personal_db_window
        
        required_methods = [
            '_setup_ui',
            '_check_activity_match',
            '_toggle_item',
            '_on_mousewheel',
            '_get_stacked_position',
        ]
        
        for method_name in required_methods:
            assert hasattr(Personal_db_window, method_name), f"Missing method: {method_name}"


class TestVirtualKeyboardClass:
    """Test VirtualKeyboard class structure"""
    
    def test_virtual_keyboard_class_exists(self):
        """Test that VirtualKeyboard class exists"""
        from src.medical_inventory import VirtualKeyboard
        
        assert VirtualKeyboard is not None
        assert hasattr(VirtualKeyboard, '__init__')
    
    def test_virtual_keyboard_has_static_method(self):
        """Test that VirtualKeyboard has get_input static method"""
        from src.medical_inventory import VirtualKeyboard
        
        assert hasattr(VirtualKeyboard, 'get_input')
        assert callable(VirtualKeyboard.get_input)
    
    def test_virtual_keyboard_has_key_methods(self):
        """Test that VirtualKeyboard has key handling methods"""
        from src.medical_inventory import VirtualKeyboard
        
        required_methods = [
            'key_press',
            'backspace',
            'clear_all',
            'toggle_shift',
            'toggle_caps',
        ]
        
        for method_name in required_methods:
            assert hasattr(VirtualKeyboard, method_name), f"Missing method: {method_name}"
    
    def test_virtual_keyboard_has_ui_methods(self):
        """Test that VirtualKeyboard has UI methods"""
        from src.medical_inventory import VirtualKeyboard
        
        required_methods = [
            '_setup_ui',
            '_center_window',
            'on_ok',
            'on_cancel',
        ]
        
        for method_name in required_methods:
            assert hasattr(VirtualKeyboard, method_name), f"Missing method: {method_name}"


# ============================================================================
# IMPORT TESTS
# ============================================================================

class TestImports:
    """Test that all required modules can be imported"""
    
    def test_main_module_imports(self):
        """Test that main module imports successfully"""
        try:
            import src.medical_inventory
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import medical_inventory: {e}")
    
    def test_constants_accessible(self):
        """Test that constants are accessible after import"""
        from src.medical_inventory import DB_FILE, REFRESH_INTERVAL, COLUMN_CONFIGS, COLUMN_LABELS
        
        assert DB_FILE is not None
        assert REFRESH_INTERVAL is not None
        assert COLUMN_CONFIGS is not None
        assert COLUMN_LABELS is not None
    
    def test_classes_accessible(self):
        """Test that classes are accessible after import"""
        from src.medical_inventory import BarcodeViewer, Personal_db_window, VirtualKeyboard
        
        assert BarcodeViewer is not None
        assert Personal_db_window is not None
        assert VirtualKeyboard is not None
    
    def test_utility_functions_accessible(self):
        """Test that utility functions are accessible"""
        from src.medical_inventory import create_round_rectangle
        
        assert create_round_rectangle is not None


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
