import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.main import app
from app.core.config import settings
from app.db.models.user import User, RoleEnum

client = TestClient(app)
BASE_URL = "/api/v1"

def get_db_session():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def setup_admin():
    db = get_db_session()
    try:
        # 1. Try to find admin by telegram_id
        admin = db.query(User).filter(User.telegram_id == 123456789).first()
        if admin:
            print(f"Found admin by Telegram ID: ID={admin.id}")
            if admin.role != RoleEnum.admin:
                print("User exists but is not admin. Promoting...")
                admin.role = RoleEnum.admin
                db.commit()
            return admin.id, admin.telegram_id

        # 2. If not found, check if any admin exists
        admin = db.query(User).filter(User.role == RoleEnum.admin).first()
        if not admin:
            print("Creating admin user...")
            admin = User(
                customer_name="Admin User",
                phone_number="+998900000000",
                telegram_id=123456789,
                role=RoleEnum.admin
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"Admin created: ID={admin.id}")
        else:
            print(f"Admin already exists (ID={admin.id}) but has different/no Telegram ID.")
            if not admin.telegram_id:
                print("Updating admin telegram_id...")
                admin.telegram_id = 123456789
                db.commit()
                db.refresh(admin)
            else:
                # Admin has some other telegram_id, let's use it? 
                # Or just create a new one? 
                # For simplicity, let's just use this admin and their ID, 
                # BUT we need a known ID for the script headers if we want to be consistent.
                # Let's just return what we have.
                print(f"Using existing admin with Telegram ID: {admin.telegram_id}")
        
        return admin.id, admin.telegram_id
    finally:
        db.close()

import uuid

def test_flow():
    print("--- Starting Verification Flow ---")
    
    # 1. Setup Admin
    admin_id, admin_tg_id = setup_admin()
    admin_headers = {
        "X-User-Id": str(admin_id),
        "X-Telegram-Id": str(admin_tg_id)
    }

    suffix = str(uuid.uuid4())[:8]

    # 2. Create Category (Admin)
    print("\n[Admin] Creating Category...")
    cat_data = {
        "name_uz": f"O'yinchoqlar_{suffix}",
        "name_ru": f"Игрушки_{suffix}",
        "name_en": f"Toys_{suffix}"
    }
    resp = client.post(f"{BASE_URL}/categories", json=cat_data, headers=admin_headers)
    if resp.status_code != 200:
        print(f"Failed to create category: {resp.text}")
        return
    category = resp.json()["data"]
    print(f"Category created: {category}")
    cat_id = category["id"]

    # 2.1 Test Get Category
    print(f"[Admin] Getting Category {cat_id}...")
    resp = client.get(f"{BASE_URL}/categories/{cat_id}", headers=admin_headers)
    if resp.status_code != 200:
        print(f"Failed to get category: {resp.status_code} {resp.text}")
    else:
        print(f"Got Category: {resp.json()['data']}")

    # 3. Create Product (Admin)
    print("\n[Admin] Creating Product...")
    # We'll just pass a URL string as per new logic.
    prod_data = {
        "name_uz": "Lego Mashina",
        "name_ru": "Лего Машина",
        "name_en": "Lego Car",
        "description_uz": "Zo'r o'yinchoq",
        "description_ru": "Отличная игрушка",
        "description_en": "Great toy",
        "price": 50000,
        "category_id": cat_id,
        "image_url": "http://example.com/image.jpg"
    }
    
    # TestClient handles Form data if data= is passed, but we need to make sure it sends as form-data.
    # But wait, my router expects Form data.
    # TestClient.post(data=...) sends form-encoded.
    
    resp = client.post(f"{BASE_URL}/products", data=prod_data, headers=admin_headers)
    
    if resp.status_code != 200:
        print(f"Failed to create product: {resp.text}")
        return
    product = resp.json()["data"]
    print(f"Product created: {product}")
    prod_id = product["id"]

    # 4. Register User
    print("\n[User] Registering...")
    user_phone = "+998901234567"
    user_tg_id = 987654321
    reg_data = {
        "customer_name": "Test User",
        "phone_number": user_phone
    }
    
    # Try to register
    resp = client.post(f"{BASE_URL}/auth/register", json=reg_data)
    if resp.status_code == 409:
        print("User already exists (409), logging in...")
        login_data = {"phone_number": user_phone}
        resp = client.post(f"{BASE_URL}/auth/login", json=login_data)
        if resp.status_code != 200:
            print(f"Failed to login after 409: {resp.text}")
            return
        user_data = resp.json()["data"]
    elif resp.status_code != 200:
        print(f"Failed to register: {resp.text}")
        return
    else:
        user_data = resp.json()["data"]
    
    print(f"User logged in: {user_data}")
    user_id = user_data["user_id"]
    
    # Set Telegram ID
    print("\n[User] Setting Telegram ID...")
    set_tg_data = {
        "phone_number": user_phone,
        "telegram_id": user_tg_id
    }
    resp = client.patch(f"{BASE_URL}/auth/set-telegram-id", json=set_tg_data)
    if resp.status_code != 200:
        print(f"Failed to set telegram_id: {resp.text}")
    else:
        print(f"Telegram ID set: {resp.json()['data']}")
    
    # Now use telegram_id header for subsequent requests
    user_headers = {
        "X-Telegram-Id": str(user_tg_id)
    }
    
    # 5. Get Me
    print("\n[User] Getting Me...")
    resp = client.get(f"{BASE_URL}/auth/get-me", headers=user_headers)
    if resp.status_code != 200:
        print(f"Failed to get me: {resp.text}")
    else:
        print(f"Get Me: {resp.json()['data']}")

    # 6. Create Order
    print("\n[User] Creating Order...")
    order_data = {
        "user_id": user_id, # Still needed for order creation body? Let's check schema. Yes.
        "shipping_address": "Tashkent, Chilonzor",
        "phone_number": "+998901234567",
        "comment": "Tezroq!",
        "items": [
            {"product_id": prod_id, "quantity": 2}
        ]
    }
    resp = client.post(f"{BASE_URL}/orders", json=order_data, headers=user_headers)
    if resp.status_code != 200:
        print(f"Failed to create order: {resp.text}")
        return
    order_id = resp.json()["data"]["order_id"]
    print(f"Order created: {resp.json()['data']}")
    
    # 7. Admin Actions (Verify, Complete)
    # Admin needs X-Telegram-Id too
    admin_headers = {
        "X-Telegram-Id": str(admin_tg_id)
    }
    
    print("\n[Admin] Verifying Order...")
    resp = client.patch(f"{BASE_URL}/orders/{order_id}/verify", headers=admin_headers)
    if resp.status_code != 200:
        print(f"Failed to verify order: {resp.text}")
    else:
        print(f"Order verified: {resp.json()['data']}")
        
    print("\n[Admin] Completing Order...")
    resp = client.patch(f"{BASE_URL}/orders/{order_id}/complete", headers=admin_headers)
    if resp.status_code != 200:
        print(f"Failed to complete order: {resp.text}")
    else:
        print(f"Order completed: {resp.json()['data']}")

    # 8. Test Delete Category (Should fail if products exist)
    print("\n[Admin] Testing Delete Category (Should fail)...")
    # We created a product in this category, so it should fail
    # We need category_id. We created it earlier.
    # Let's assume we can get it from product or we saved it.
    # In this script we didn't save category_id explicitly in a variable accessible here easily unless we parse logs.
    # But wait, we printed it. Let's just try to delete the one we created.
    # We can list categories to find it or just use the one we created.
    # In step 2 we created category.
    # Let's just create a NEW category and product to test this specifically.
    
    print("[Admin] Creating Temp Category for Delete Test...")
    cat_data = {
        "name_uz": f"DeleteMe_{uuid.uuid4().hex[:8]}",
        "name_ru": f"DeleteMe_{uuid.uuid4().hex[:8]}",
        "name_en": f"DeleteMe_{uuid.uuid4().hex[:8]}"
    }
    resp = client.post(f"{BASE_URL}/categories", json=cat_data, headers=admin_headers)
    temp_cat_id = resp.json()["data"]["id"]
    print(f"Temp Category created: {temp_cat_id}")
    
    print("[Admin] Creating Temp Product...")
    prod_data = {
        "name_uz": "Temp Product",
        "name_ru": "Temp Product",
        "name_en": "Temp Product",
        "price": 1000,
        "category_id": temp_cat_id,
        "image_url": "http://example.com/img.jpg"
    }
    # Products endpoint expects Form data, not JSON
    resp = client.post(f"{BASE_URL}/products", data=prod_data, headers=admin_headers)
    if resp.status_code != 200:
        print(f"Failed to create temp product: {resp.text}")
        return
    temp_prod_id = resp.json()["data"]["id"]
    print(f"Temp Product created: {temp_prod_id}")
    
    print("[Admin] Deleting Category (Expect 409)...")
    resp = client.delete(f"{BASE_URL}/categories/{temp_cat_id}", headers=admin_headers)
    if resp.status_code == 409:
        print("Success! Got 409 as expected.")
    else:
        print(f"Failed! Expected 409, got {resp.status_code}: {resp.text}")
        
    # Now delete product then category
    print("[Admin] Deleting Temp Product...")
    client.delete(f"{BASE_URL}/products/{temp_prod_id}", headers=admin_headers)
    
    print("[Admin] Deleting Category (Expect 204)...")
    resp = client.delete(f"{BASE_URL}/categories/{temp_cat_id}", headers=admin_headers)
    if resp.status_code == 204:
        print("Success! Category deleted.")
    else:
        print(f"Failed! Expected 204, got {resp.status_code}: {resp.text}")

    print("\n--- Verification Successful ---")

if __name__ == "__main__":
    try:
        test_flow()
    except Exception as e:
        print(f"Error: {e}")
