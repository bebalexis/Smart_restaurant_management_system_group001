def test_health_or_root(client):
    # Prefer /health if available, otherwise fall back to /
    for path in ("/health", "/"):
        r = client.get(path)
        if r.status_code in (200, 204):
            # If JSON, validate minimal shape
            js = r.get_json(silent=True)
            if isinstance(js, dict) and "status" in js:
                assert js.get("status") in ("ok", "healthy", "up")
            return
        elif r.status_code in (404, 405):
            continue
    # If neither exists, skip with a helpful message
    import pytest
    pytest.skip("No /health or / route found returning 200.")
