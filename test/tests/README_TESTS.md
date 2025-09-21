# SRMS Expanded – Pytest Suite

Drop this `tests/` folder (and `pytest.ini`) into the root of your **srms_expanded** project.

## Quick Start
```bash
# from your project root (where app.py lives)
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt || pip install flask flask_sqlalchemy pytest pytest-cov itsdangerous werkzeug
pytest -v
```

## What these tests cover
- **Basic app health** (`/health` or `/`) and template sanity
- **Auth**: `/login` using either token (JWT) or session cookie
- **Menu & Tables**: list and create
- **Reservations**: create and list
- **Orders & Payments**: create simple order and pay, then check `/reports/sales`

> The tests are defensive: if an endpoint is missing (`404`/`405`) or requires auth but no token is returned, the test will **skip** with a helpful message instead of failing the whole run. You can then wire up the missing route or tweak the test to match your API.

## Assumptions
- `create_app(testing=True)` exists in `app.py` (or `create_app()` returns a Flask app)
- `models.py` exposes `db` and `User`
- Admin user is seeded in a **fresh in-memory SQLite DB** for tests
- `/login` accepts JSON `{ "username": "admin", "password": "password" }` and either:
  - returns `{"token": "..."}` (JWT/bearer), or
  - sets a session cookie (no token field).

## Adjustments
If your endpoints or payloads differ, open the relevant test file and change the minimal payloads near the top. Each test has clear comments and small helper functions to keep changes easy.
