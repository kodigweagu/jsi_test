import os
import sys
from pathlib import Path

# Ensure project root is importable
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

# Force all tests to use test_resources
os.environ["RESOURCES_DIR"] = "test_resources"
