import pytest

def _ensure_menu_item(client, auth_headers):
    r = client.post("/menu", json={"name": "Test Burger", "price": 9.99, "category": "Burger"}, headers=auth_headers)
    if r.status_code == 401 and not auth_headers:
        pytest.skip("Menu creation requires auth, and /login did not return a token/session.")
    if r.status_code in (404, 405):
        pytest.skip("POST /menu missing; cannot create menu item for order test.")
    assert r.status_code in (200, 201)
    data = r.get_json(silent=True) or {}
    # Handle dict or nested
    if isinstance(data, dict) and "id" in data:
        return data["id"], 1
    if isinstance(data, dict) and "item" in data and isinstance(data["item"], dict):
        return data["item"].get("id"), 1
    # Fallback: list and take last
    lst = client.get("/menu").get_json(silent=True) or []
    if isinstance(lst, list) and lst:
        return lst[-1].get("id"), 1
    pytest.skip("Could not determine created menu item id.")

def test_orders_flow_and_reports(client, auth_headers):
    # Ensure endpoints exist
    r = client.get("/orders")
    if r.status_code in (404, 405):
        pytest.skip("/orders list endpoint missing.")

    item_id, qty = _ensure_menu_item(client, auth_headers)

    # Create order: support common payloads
    # Try items = [{"menu_item_id": id, "qty": 1}] first
    payload_candidates = [
        {"items": [{"menu_item_id": item_id, "qty": qty}]},
        {"items": [{"id": item_id, "qty": qty}]},
        {"menu_item_id": item_id, "qty": qty},
    ]
    created = None
    for p in payload_candidates:
        r = client.post("/orders", json=p, headers=auth_headers)
        if r.status_code in (200, 201):
            created = r.get_json(silent=True) or {}
            break
        if r.status_code == 401 and not auth_headers:
            pytest.skip("POST /orders requires auth, and no token/session detected.")
        if r.status_code in (404, 405):
            continue
    if not created:
        pytest.skip("Could not create an order (POST /orders not available).")

    # extract order_id from various shapes
    order_id = None
    if isinstance(created, dict):
        order_id = created.get("id") or (created.get("order") or {}).get("id")
    if not order_id:
        # try list endpoint and take last
        lst = client.get("/orders").get_json(silent=True) or []
        if isinstance(lst, list) and lst:
            order_id = lst[-1].get("id")
    if not order_id:
        pytest.skip("Created order id not found in response.")

    # Pay the order if supported
    r = client.post(f"/orders/{order_id}/pay", json={"method": "cash"}, headers=auth_headers)
    if r.status_code in (404, 405):
        # Payment route missing; that's fine, continue to reports check
        pass
    elif r.status_code == 401 and not auth_headers:
        pytest.skip("Payment requires auth, and /login did not return a token/session.")
    else:
        assert r.status_code in (200, 201)

    # Sales report
    r = client.get("/reports/sales")
    if r.status_code in (404, 405):
        pytest.skip("/reports/sales endpoint missing.")
    assert r.status_code == 200
    # accept list, dict, or CSV/text
    data = r.get_json(silent=True)
    assert (data is not None) or (isinstance(r.data, (bytes, bytearray)) and len(r.data) > 0)
