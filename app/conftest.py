import os
import sys

# Ensure app module is found
sys.path.append(os.getcwd())

# Set default DATABASE_URL for tests if not present
if "DATABASE_URL" not in os.environ:
    from dotenv import load_dotenv
    # Try loading from parent directory if in app/
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    
    if "DATABASE_URL" not in os.environ:
        # Fallback
        os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/toys_catalog"

import pytest
