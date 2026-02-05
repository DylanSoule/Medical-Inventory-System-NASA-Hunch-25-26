"""
Pytest configuration for Medical Inventory System tests
"""

import sys
import os

# Add project directories to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'Database'))

# Set test environment variables
os.environ['TESTING'] = 'true'
