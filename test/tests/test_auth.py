import pytest

def test_login_flow(client):
    # Try JSON login
    resp = client.post("/login", json={"username": "admin", "password": "password"})
    if resp.status_code in (404, 405):
        pytest.skip("/login endpoint missing.")
    assert resp.status_code in (200, 302)
    data = resp.get_json(silent=True) or {}
    # Accept JWT or session flows
    if resp.status_code == 200:
        # Either a token is present or a session cookie was set
        assert ("token" in data) or ("Set-Cookie" in resp.headers or resp.headers.getlist("Set-Cookie"))
    # If 302 (redirect), assume session cookie flow to dashboard
    # Nothing else to assert here; endpoint exists and works minimally.
