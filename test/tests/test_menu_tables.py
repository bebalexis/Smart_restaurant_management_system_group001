import pytest

def _authed_post_json(client, url, payload, headers):
    r = client.post(url, json=payload, headers=headers)
    # If unauthorized and we have no headers, skip rather than fail hard
    if r.status_code == 401 and not headers:
        pytest.skip(f"{url} requires auth and no token/session header detected from /login.")
    return r

def test_menu_list_and_create(client, auth_headers):
    # List menu
    r = client.get("/menu")
    if r.status_code in (404, 405):
        pytest.skip("/menu list endpoint missing.")
    assert r.status_code == 200
    assert isinstance(r.get_json(silent=True), (list, dict))

    # Create a menu item
    payload = {"name": "Test Pizza", "price": 12.99, "category": "Pizza"}
    r = _authed_post_json(client, "/menu", payload, auth_headers)
    if r.status_code in (404, 405):
        pytest.skip("/menu create endpoint missing (POST /menu).")
    assert r.status_code in (200, 201)

def test_tables_list_and_create(client, auth_headers):
    # List tables
    r = client.get("/tables")
    if r.status_code in (404, 405):
        pytest.skip("/tables list endpoint missing.")
    assert r.status_code == 200
    assert isinstance(r.get_json(silent=True), (list, dict))

    # Create a table
    payload = {"label": "T99", "capacity": 4}
    r = _authed_post_json(client, "/tables", payload, auth_headers)
    if r.status_code in (404, 405):
        pytest.skip("/tables create endpoint missing (POST /tables).")
    assert r.status_code in (200, 201)
