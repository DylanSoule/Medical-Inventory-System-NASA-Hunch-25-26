"""
Pytest configuration for Medical Inventory System tests
"""

import sys
import os
from unittest.mock import MagicMock
from enum import Enum

# Add project directories to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'Database'))

# Mock facial recognition error enum
class MockFaceRecognitionError(Enum):
    """Mock FaceRecognitionError enum for testing"""
    SUCCESS = "success"
    CAMERA_ERROR = "camera_error"
    REFERENCE_FOLDER_ERROR = "reference_folder_error"
    MODEL_LOAD_FAILED = "model_load_failed"
    PRELOAD_FAILED = "preload_failed"
    CAMERA_DISCONNECTED = "camera_disconnected"
    FRAME_CAPTURE_FAILED = "frame_capture_failed"

# Create comprehensive mock for facial_recognition module
def create_facial_recognition_mock():
    """Create a mock facial_recognition module"""
    mock_fr = MagicMock()
    mock_fr.FaceRecognitionError = MockFaceRecognitionError
    mock_fr.preload_everything = MagicMock(return_value=MockFaceRecognitionError.SUCCESS)
    mock_fr.quick_detect = MagicMock(return_value=["test_user"])
    mock_fr.main = MagicMock(return_value=["test_user"])
    mock_fr.reinitialize_camera = MagicMock(return_value=True)
    mock_fr.preloading_complete = True
    mock_fr.camera_ready = True
    return mock_fr

# Mock facial_recognition before any imports
mock_facial_recognition = create_facial_recognition_mock()
sys.modules['facial_recognition'] = mock_facial_recognition
sys.modules['src.facial_recognition'] = mock_facial_recognition

# Set test environment variables
os.environ['TESTING'] = 'true'
