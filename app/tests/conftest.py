import os
import sys

# Ensure app module is found
sys.path.append(os.getcwd())

# Set default DATABASE_URL for tests if not present
if "DATABASE_URL" not in os.environ:
    # Try to read from .env manually if needed, or set a default test DB
    # For now, let's assume the user wants to use the local DB or a test variant.
    # If .env exists, python-dotenv (used by pydantic-settings) should load it, 
    # BUT pydantic-settings loads it when Settings() is instantiated.
    # If we are here, it means Settings() might have failed or we want to be sure.
    # Let's try to load .env explicitly to be safe, or set a dummy one to pass validation
    # if we plan to mock the DB engine anyway.
    # However, our tests use the real DB engine from app.db.session.
    # So we need a real connection string.
    from dotenv import load_dotenv
    load_dotenv()
    
    if "DATABASE_URL" not in os.environ:
        # Fallback for CI/CD or if .env is missing
        os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/toys_catalog"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.core.deps import get_db
from app.core.config import settings
from app.db.models.user import User, RoleEnum
import uuid

# Use a separate test database or in-memory SQLite for speed/isolation
# For simplicity in this setup, we might use the same DB but with transaction rollbacks,
# or a separate test DB URL if configured. 
# Given the environment, let's use the existing DB but wrap tests in transactions (if possible) 
# or just be careful. Ideally, we use a separate test DB.
# Let's assume we use the main DB for now but ideally we should override it.

client = TestClient(app)

@pytest.fixture(scope="module")
def test_client():
    yield client

@pytest.fixture(scope="module")
def admin_headers():
    # Ensure admin exists
    admin_phone = "+998999999999"
    admin_tid = 999999999
    
    # Try to register as admin (if endpoint exists) or just insert into DB
    # Since we don't have a public register-admin endpoint that is open, 
    # we should rely on the init admin or create one via DB.
    # But we don't want to mess with DB session here if possible.
    # Let's use the one from settings, but make sure it's registered.
    
    # Actually, let's use the /auth/register-admin endpoint if we added it for testing/setup
    # or just use the INIT_ADMIN credentials.
    
    # Let's try to register a new admin to be safe.
    try:
        client.post("/api/v1/auth/register-admin", json={
            "customer_name": "Test Admin",
            "phone_number": admin_phone
        })
        client.patch("/api/v1/auth/set-telegram-id", json={
            "phone_number": admin_phone,
            "telegram_id": admin_tid
        })
    except Exception:
        pass
        
    return {"X-Telegram-Id": str(admin_tid)}

@pytest.fixture(scope="module")
def user_headers():
    # Create a random user
    phone = f"+9989{uuid.uuid4().int % 100000000:08d}"
    tid = (uuid.uuid4().int % 1000000000)
    
    # Register
    resp = client.post("/api/v1/auth/register", json={"customer_name": "Test User", "phone_number": phone})
    if resp.status_code == 409:
        # login
        pass
    
    # Set Telegram ID
    client.patch("/api/v1/auth/set-telegram-id", json={"phone_number": phone, "telegram_id": tid})
    
    return {"X-Telegram-Id": str(tid)}
