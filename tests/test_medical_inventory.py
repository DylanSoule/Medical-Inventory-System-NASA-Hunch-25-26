"""
Test Suite for Medical Inventory System
NASA HUNCH Project 2025-26

This module contains unit tests for the medical inventory application.
Tests focus on UI rendering and functionality.
"""

import pytest
import sys
import os
import datetime
from unittest.mock import Mock, patch, MagicMock, PropertyMock, call
import tkinter as tk

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
# UI RENDERING TESTS
# ============================================================================

class TestUIRendering:
    """Test UI component rendering and initialization"""
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_main_window_initialization(self, mock_fr, mock_db):
        """Test that main window initializes without errors"""
        from src.medical_inventory import BarcodeViewer
        
        mock_fr.preload_everything.return_value = Mock()
        mock_fr.preloading_complete = True
        mock_fr.camera_ready = True
        mock_db.return_value.pull_data.return_value = []
        
        try:
            # Create root window without entering mainloop
            with patch.object(BarcodeViewer, 'mainloop', lambda x: None):
                app = BarcodeViewer()
                assert app is not None
                assert hasattr(app, 'tree')
                assert hasattr(app, 'search_var')
                assert hasattr(app, 'filter_var')
                app.destroy()
        except tk.TclError:
            pytest.skip("No display available for UI test")
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_sidebar_creation(self, mock_fr, mock_db):
        """Test that sidebar is created with all components"""
        from src.medical_inventory import BarcodeViewer
        
        mock_db.return_value.pull_data.return_value = []
        
        try:
            with patch.object(BarcodeViewer, 'mainloop', lambda x: None):
                app = BarcodeViewer()
                
                # Check sidebar components exist
                assert hasattr(app, 'search_var')
                assert hasattr(app, 'filter_var')
                assert hasattr(app, 'low_stock_var')
                assert hasattr(app, 'column_visibility')
                
                app.destroy()
        except tk.TclError:
            pytest.skip("No display available for UI test")
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_treeview_creation(self, mock_fr, mock_db):
        """Test that treeview is created with correct columns"""
        from src.medical_inventory import BarcodeViewer, COLUMN_CONFIGS
        
        mock_db.return_value.pull_data.return_value = []
        
        try:
            with patch.object(BarcodeViewer, 'mainloop', lambda x: None):
                app = BarcodeViewer()
                
                # Verify tree exists
                assert hasattr(app, 'tree')
                
                # Verify all columns are configured
                tree_columns = app.tree['columns']
                for col in COLUMN_CONFIGS.keys():
                    assert col in tree_columns
                
                app.destroy()
        except tk.TclError:
            pytest.skip("No display available for UI test")
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_action_buttons_creation(self, mock_fr, mock_db):
        """Test that all action buttons are created"""
        from src.medical_inventory import BarcodeViewer
        
        mock_db.return_value.pull_data.return_value = []
        
        try:
            with patch.object(BarcodeViewer, 'mainloop', lambda x: None):
                app = BarcodeViewer()
                
                # Check buttons exist
                assert hasattr(app, 'log_scan_btn')
                assert hasattr(app, 'personal_db_btn')
                
                app.destroy()
        except tk.TclError:
            pytest.skip("No display available for UI test")


# ============================================================================
# FUNCTIONALITY TESTS
# ============================================================================

class TestDataFiltering:
    """Test search and filter functionality"""
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_search_functionality(self, mock_fr, mock_db):
        """Test search filter works correctly"""
        from src.medical_inventory import BarcodeViewer
        
        # Mock database data
        test_data = [
            ('12345', 'Aspirin', 100, '2025-12-31', 'pill', 'medication', '100mg', 'A1'),
            ('67890', 'Ibuprofen', 50, '2025-11-30', 'pill', 'medication', '200mg', 'A2'),
        ]
        mock_db.return_value.pull_data.return_value = test_data
        
        try:
            with patch.object(BarcodeViewer, 'mainloop', lambda x: None):
                app = BarcodeViewer()
                
                # Set search term
                app.search_var.set("aspirin")
                app.apply_search_filter()
                
                # Verify filtered results
                items = app.tree.get_children()
                assert len(items) == 1
                
                # Clear search
                app.search_var.set("")
                app.apply_search_filter()
                items = app.tree.get_children()
                assert len(items) == 2
                
                app.destroy()
        except tk.TclError:
            pytest.skip("No display available for UI test")
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_expiration_filter(self, mock_fr, mock_db):
        """Test expiration date filtering"""
        from src.medical_inventory import BarcodeViewer
        
        # Create test data with different expiration dates
        today = datetime.date.today()
        expired_date = (today - datetime.timedelta(days=10)).strftime("%Y-%m-%d")
        expiring_soon = (today + datetime.timedelta(days=15)).strftime("%Y-%m-%d")
        far_future = (today + datetime.timedelta(days=100)).strftime("%Y-%m-%d")
        
        test_data = [
            ('11111', 'Expired Drug', 10, expired_date, 'pill', 'medication', '10mg', 'A1'),
            ('22222', 'Expiring Soon', 20, expiring_soon, 'pill', 'medication', '20mg', 'A2'),
            ('33333', 'Future Drug', 30, far_future, 'pill', 'medication', '30mg', 'A3'),
        ]
        mock_db.return_value.pull_data.return_value = test_data
        
        try:
            with patch.object(BarcodeViewer, 'mainloop', lambda x: None):
                app = BarcodeViewer()
                
                # Test "Expired" filter
                app.filter_var.set("Expired")
                app.apply_search_filter()
                items = app.tree.get_children()
                assert len(items) == 1
                
                # Test "Expiring Soon" filter
                app.filter_var.set("Expiring Soon")
                app.apply_search_filter()
                items = app.tree.get_children()
                assert len(items) == 1
                
                # Test "All" filter
                app.filter_var.set("All")
                app.apply_search_filter()
                items = app.tree.get_children()
                assert len(items) == 3
                
                app.destroy()
        except tk.TclError:
            pytest.skip("No display available for UI test")
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_low_stock_filter(self, mock_fr, mock_db):
        """Test low stock filtering"""
        from src.medical_inventory import BarcodeViewer
        
        test_data = [
            ('11111', 'Low Stock Item', 5, '2025-12-31', 'pill', 'medication', '10mg', 'A1'),
            ('22222', 'Normal Stock', 100, '2025-12-31', 'pill', 'medication', '20mg', 'A2'),
        ]
        mock_db.return_value.pull_data.return_value = test_data
        
        try:
            with patch.object(BarcodeViewer, 'mainloop', lambda x: None):
                app = BarcodeViewer()
                
                # Enable low stock filter
                app.low_stock_var.set(True)
                app.apply_search_filter()
                items = app.tree.get_children()
                assert len(items) == 1
                
                # Disable low stock filter
                app.low_stock_var.set(False)
                app.apply_search_filter()
                items = app.tree.get_children()
                assert len(items) == 2
                
                app.destroy()
        except tk.TclError:
            pytest.skip("No display available for UI test")


class TestColumnVisibility:
    """Test column visibility toggle functionality"""
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_column_toggle(self, mock_fr, mock_db):
        """Test toggling column visibility"""
        from src.medical_inventory import BarcodeViewer
        
        mock_db.return_value.pull_data.return_value = []
        
        try:
            with patch.object(BarcodeViewer, 'mainloop', lambda x: None):
                app = BarcodeViewer()
                
                # Initially all columns visible
                visible_cols = [col for col, var in app.column_visibility.items() if var.get()]
                assert len(visible_cols) == 8
                
                # Hide a column
                app.column_visibility['barcode'].set(False)
                app.update_column_visibility()
                
                visible_cols = [col for col, var in app.column_visibility.items() if var.get()]
                assert len(visible_cols) == 7
                assert 'barcode' not in visible_cols
                
                app.destroy()
        except tk.TclError:
            pytest.skip("No display available for UI test")


class TestDialogs:
    """Test dialog windows"""
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_show_popup(self, mock_fr, mock_db):
        """Test popup dialog creation"""
        from src.medical_inventory import BarcodeViewer
        
        mock_db.return_value.pull_data.return_value = []
        
        try:
            with patch.object(BarcodeViewer, 'mainloop', lambda x: None):
                app = BarcodeViewer()
                
                # Mock wait_window to prevent blocking
                with patch.object(app, 'wait_window', lambda x: None):
                    # Test that popup doesn't crash
                    app.show_popup("Test Title", "Test Message", "info")
                    app.show_popup("Test Error", "Error Message", "error")
                    app.show_popup("Test Warning", "Warning Message", "warning")
                
                app.destroy()
        except tk.TclError:
            pytest.skip("No display available for UI test")
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_show_confirm(self, mock_fr, mock_db):
        """Test confirmation dialog"""
        from src.medical_inventory import BarcodeViewer
        
        mock_db.return_value.pull_data.return_value = []
        
        try:
            with patch.object(BarcodeViewer, 'mainloop', lambda x: None):
                app = BarcodeViewer()
                
                # Mock wait_window to prevent blocking
                with patch.object(app, 'wait_window', lambda x: None):
                    result = app.show_confirm("Test Confirm", "Are you sure?")
                    # Result should be False since we didn't click Yes
                    assert result == False
                
                app.destroy()
        except tk.TclError:
            pytest.skip("No display available for UI test")


class TestTreeviewInteraction:
    """Test treeview interaction functionality"""
    
    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_tree_selection(self, mock_fr, mock_db):
        """Test tree row selection"""
        from src.medical_inventory import BarcodeViewer
        
        test_data = [
            ('11111', 'Item 1', 10, '2025-12-31', 'pill', 'medication', '10mg', 'A1'),
            ('22222', 'Item 2', 20, '2025-12-31', 'pill', 'medication', '20mg', 'A2'),
        ]
        mock_db.return_value.pull_data.return_value = test_data
        
        try:
            with patch.object(BarcodeViewer, 'mainloop', lambda x: None):
                app = BarcodeViewer()
                
                # Get items in tree
                items = app.tree.get_children()
                assert len(items) == 2
                
                # Select first item
                app.tree.selection_set(items[0])
                selection = app.tree.selection()
                assert len(selection) == 1
                
                # Select multiple items
                app.tree.selection_set(items)
                selection = app.tree.selection()
                assert len(selection) == 2
                
                app.destroy()
        except tk.TclError:
            pytest.skip("No display available for UI test")


class TestVirtualKeyboard:
    """Test virtual keyboard functionality"""
    
    def test_virtual_keyboard_class_exists(self):
        """Test VirtualKeyboard class can be imported"""
        from src.medical_inventory import VirtualKeyboard
        assert VirtualKeyboard is not None
    
    def test_virtual_keyboard_has_methods(self):
        """Test VirtualKeyboard has required methods"""
        from src.medical_inventory import VirtualKeyboard
        
        required_methods = ['key_press', 'backspace', 'clear_all', 'toggle_shift', 'toggle_caps']
        for method in required_methods:
            assert hasattr(VirtualKeyboard, method)


class TestPersonalDatabase:
    """Test personal database window"""
    
    def test_personal_db_window_class_exists(self):
        """Test Personal_db_window class exists"""
        from src.medical_inventory import Personal_db_window
        assert Personal_db_window is not None
    
    def test_personal_db_has_timeline_methods(self):
        """Test timeline methods exist"""
        from src.medical_inventory import Personal_db_window
        
        required_methods = ['load_timeline_data', 'draw_timeline', 'zoom_in', 'zoom_out', 'reset_zoom']
        for method in required_methods:
            assert hasattr(Personal_db_window, method)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFullWorkflow:
    """Test complete user workflows"""

    @patch('src.medical_inventory.DatabaseManager')
    @patch('src.medical_inventory.fr')
    def test_search_and_filter_workflow(self, mock_fr, mock_db):
        """Test combined search and filter workflow"""
        from src.medical_inventory import BarcodeViewer
        
        today = datetime.date.today()
        expiring_soon = (today + datetime.timedelta(days=15)).strftime("%Y-%m-%d")
        
        test_data = [
            ('11111', 'Aspirin Low', 5, expiring_soon, 'pill', 'medication', '10mg', 'A1'),
            ('22222', 'Aspirin High', 100, '2026-12-31', 'pill', 'medication', '20mg', 'A2'),
            ('33333', 'Ibuprofen Low', 8, expiring_soon, 'pill', 'medication', '15mg', 'A3'),
        ]
        mock_db.return_value.pull_data.return_value = test_data
        
        try:
            with patch.object(BarcodeViewer, 'mainloop', lambda x: None):
                app = BarcodeViewer()
                
                # All items initially
                items = app.tree.get_children()
                assert len(items) == 3
                
                # Search for "aspirin"
                app.search_var.set("aspirin")
                app.apply_search_filter()
                items = app.tree.get_children()
                assert len(items) == 2
                
                # Add "expiring soon" filter
                app.filter_var.set("Expiring Soon")
                app.apply_search_filter()
                items = app.tree.get_children()
                assert len(items) == 1
                
                # Add low stock filter
                app.low_stock_var.set(True)
                app.apply_search_filter()
                items = app.tree.get_children()
                assert len(items) == 1
                
                # Clear all filters
                app.search_var.set("")
                app.filter_var.set("All")
                app.low_stock_var.set(False)
                app.apply_search_filter()
                items = app.tree.get_children()
                assert len(items) == 3
                
                app.destroy()
        except tk.TclError:
            pytest.skip("No display available for UI test")


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
