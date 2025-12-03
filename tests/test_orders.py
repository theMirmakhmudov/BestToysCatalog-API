def test_order_flow(test_client, admin_headers, user_headers):
    import uuid
    # Setup: Create Category and Product
    unique_id = uuid.uuid4().hex[:8]
    resp = test_client.post("/api/v1/categories", json={
        "name_uz": f"OrderCat_uz_{unique_id}", 
        "name_ru": f"OrderCat_ru_{unique_id}", 
        "name_en": f"OrderCat_en_{unique_id}"
    }, headers=admin_headers)
    cat_id = resp.json()["data"]["id"]
    
    resp = test_client.post("/api/v1/products", data={
        "name_uz": f"OrderProd_{unique_id}", 
        "name_ru": f"OrderProd_{unique_id}", 
        "name_en": f"OrderProd_{unique_id}",
        "price": 500, "category_id": cat_id, "image_url": "http://img.com"
    }, headers=admin_headers)
    prod_id = resp.json()["data"]["id"]
    
    # User: Create Order
    # Need user_id. user_headers has X-Telegram-Id. 
    # We need to get the user_id from /auth/get-me or assume we know it.
    # Let's call get-me
    resp = test_client.get("/api/v1/auth/get-me", headers=user_headers)
    user_id = resp.json()["data"]["id"]
    
    order_data = {
        "user_id": user_id,
        "shipping_address": "Tashkent",
        "phone_number": "+998901234567",
        "items": [{"product_id": prod_id, "quantity": 2}]
    }
    resp = test_client.post("/api/v1/orders", json=order_data, headers=user_headers)
    assert resp.status_code == 200
    order_id = resp.json()["data"]["order_id"]
    assert resp.json()["data"]["status"] == "checking"
    
    # Admin: Verify
    resp = test_client.patch(f"/api/v1/orders/{order_id}/verify", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "verified"
    
    # Admin: Complete
    resp = test_client.patch(f"/api/v1/orders/{order_id}/complete", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "done"

def test_order_rbac(test_client, user_headers):
    # User cannot verify order
    # Create a dummy order first (or fail on non-existent)
    # Just check 403 on verify endpoint
    resp = test_client.patch("/api/v1/orders/99999/verify", headers=user_headers)
    # Should be 403 Forbidden (or 404 if check order exists first, but RBAC usually first)
    # Implementation checks order existence first then RBAC? 
    # Let's check code: get_db -> get order -> check RBAC.
    # So if order 99999 doesn't exist, it returns 404.
    # We need a real order to test RBAC properly or rely on 403 if we hit it.
    # Actually, verify endpoint has `admin=Depends(admin_required)`.
    # So it should return 403 immediately if not admin.
    assert resp.status_code == 403
