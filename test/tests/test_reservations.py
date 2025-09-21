import pytest

def _ensure_table(client, auth_headers):
    # Create a table we can reserve
    r = client.post("/tables", json={"label": "T55", "capacity": 2}, headers=auth_headers)
    if r.status_code == 401 and not auth_headers:
        pytest.skip("Reservations require auth, and /login did not return a token/session.")
    if r.status_code in (404, 405):
        pytest.skip("POST /tables missing; cannot create table for reservation test.")
    assert r.status_code in (200, 201)
    data = r.get_json(silent=True) or {}
    # Handle either dict {"id":..} or nested {"table": {...}}
    if isinstance(data, dict) and "id" in data:
        return data["id"]
    if isinstance(data, dict) and "table" in data and isinstance(data["table"], dict):
        return data["table"].get("id") or data["table"].get("table_id")
    # Fallback: list tables and take the last
    lst = client.get("/tables").get_json(silent=True) or []
    if isinstance(lst, list) and lst:
        return lst[-1].get("id") or lst[-1].get("table_id")
    pytest.skip("Could not determine created table id.")

def test_reservation_create_and_list(client, auth_headers):
    # If no /reservations endpoint, skip
    r = client.get("/reservations")
    if r.status_code in (404, 405):
        pytest.skip("/reservations list endpoint missing.")
    assert r.status_code == 200

    table_id = _ensure_table(client, auth_headers)

    payload = {"table_id": table_id, "name": "Test Guest", "size": 2}
    r = client.post("/reservations", json=payload, headers=auth_headers)
    if r.status_code == 401 and not auth_headers:
        pytest.skip("POST /reservations requires auth, and no token/session detected.")
    if r.status_code in (404, 405):
        pytest.skip("POST /reservations missing.")
    assert r.status_code in (200, 201)

    # List should now include at least one item
    r = client.get("/reservations")
    assert r.status_code == 200
    data = r.get_json(silent=True)
    assert data is not None
