import sys
import os

# Make sure backend folder is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app