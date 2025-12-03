import uuid

def test_category_crud(test_client, admin_headers):
    # Create
    name_base = f"Cat_{uuid.uuid4().hex[:6]}"
    resp = test_client.post("/api/v1/categories", json={
        "name_uz": name_base + "_uz",
        "name_ru": name_base + "_ru",
        "name_en": name_base + "_en"
    }, headers=admin_headers)
    assert resp.status_code == 200
    cat_id = resp.json()["data"]["id"]
    
    # Get
    resp = test_client.get(f"/api/v1/categories/{cat_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["name_uz"] == name_base + "_uz"
    
    # Update
    resp = test_client.put(f"/api/v1/categories/{cat_id}", json={
        "name_en": name_base + "_en_updated"
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["name_en"] == name_base + "_en_updated"
    
    # Delete (Success)
    resp = test_client.delete(f"/api/v1/categories/{cat_id}", headers=admin_headers)
    assert resp.status_code == 204
    
    # Get (Not Found)
    resp = test_client.get(f"/api/v1/categories/{cat_id}")
    assert resp.status_code == 404

def test_product_crud(test_client, admin_headers):
    # Create Category first
    resp = test_client.post("/api/v1/categories", json={
        "name_uz": "ProdCat_uz", "name_ru": "ProdCat_ru", "name_en": "ProdCat_en"
    }, headers=admin_headers)
    cat_id = resp.json()["data"]["id"]
    
    # Create Product
    resp = test_client.post("/api/v1/products", data={
        "name_uz": "P_uz", "name_ru": "P_ru", "name_en": "P_en",
        "price": 100, "category_id": cat_id, "image_url": "http://img.com"
    }, headers=admin_headers)
    assert resp.status_code == 200
    prod_id = resp.json()["data"]["id"]
    
    # Get
    resp = test_client.get(f"/api/v1/products/{prod_id}")
    assert resp.status_code == 200
    
    # Update
    resp = test_client.put(f"/api/v1/products/{prod_id}", data={"price": 200}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["price"] == 200.0
    
    # Delete Category Fail (Integrity)
    resp = test_client.delete(f"/api/v1/categories/{cat_id}", headers=admin_headers)
    assert resp.status_code == 409
    
    # Delete Product
    resp = test_client.delete(f"/api/v1/products/{prod_id}", headers=admin_headers)
    assert resp.status_code == 204
    
    # Delete Category Success
    resp = test_client.delete(f"/api/v1/categories/{cat_id}", headers=admin_headers)
    assert resp.status_code == 204
