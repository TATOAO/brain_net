"""
Brain_Net Backend Application Package
"""

__version__ = "1.0.0"

import sys
import os

# Add the project root to the Python path to import from shared
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root) 