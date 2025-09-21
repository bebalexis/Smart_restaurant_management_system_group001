"""
Project: Smart Restaurant Management System (SRMS)
School: UMGC – Software Development and Security
Authors: Beby Alexis, Kevin Wong , David White Jr
Date: October 2025

Description:
Unit and integration tests for order creation, listing, and payment.
Ensures correctness and contributes to 90%+ coverage.
"""



import os, sys, importlib
import pytest
from werkzeug.security import generate_password_hash

# --- Make sure project root is importable ---
# Add CWD and the parent of the tests folder to sys.path
CWD = os.getcwd()
TESTS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = CWD if os.path.exists(os.path.join(CWD, "requirements.txt")) or os.path.exists(os.path.join(CWD, "app.py")) else os.path.abspath(os.path.join(TESTS_DIR, os.pardir))

for p in {CWD, TESTS_DIR, PROJECT_ROOT}:
    if p not in sys.path:
        sys.path.insert(0, p)

# --- Try to locate the Flask app or factory in common places ---
APP_CANDIDATES = [
    # (module, factory_attr, instance_attr)
    ("app", "create_app", "app"),
    ("application", "create_app", "app"),
    ("main", "create_app", "app"),
    ("wsgi", "create_app", "app"),
    ("wsgi", None, "application"),           # gunicorn style: application = Flask(...)
    ("backend.app", "create_app", "app"),
    ("backend.wsgi", "create_app", "app"),
    ("srms.app", "create_app", "app"),
    ("srms_expanded.app", "create_app", "app"),
]

def _import_first_hit():
    last_err = None
    for mod_name, factory_attr, instance_attr in APP_CANDIDATES:
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:
            last_err = e
            continue
        # Prefer factory if present & callable
        if factory_attr and hasattr(mod, factory_attr) and callable(getattr(mod, factory_attr)):
            return getattr(mod, factory_attr)
        # else try an app instance attribute
        if instance_attr and hasattr(mod, instance_attr):
            return getattr(mod, instance_attr)
    # final fallback: if there's an app.py in root, import it directly
    if os.path.exists(os.path.join(PROJECT_ROOT, "app.py")):
        try:
            spec = importlib.util.spec_from_file_location("app", os.path.join(PROJECT_ROOT, "app.py"))
            module = importlib.util.module_from_spec(spec)
            sys.modules["app"] = module
            spec.loader.exec_module(module)  # type: ignore
            # Try common names again
            for name in ("create_app", "app"):
                if hasattr(module, name):
                    return getattr(module, name)
        except Exception as e:
            last_err = e
    raise ImportError(
        f"Could not locate your Flask app. Tried modules: {[c[0] for c in APP_CANDIDATES]}. "
        f"Make sure your project exposes either a factory `create_app()` or an app instance `app` (or `application`). "
        f"Last error: {last_err}"
    )

_app_or_factory = _import_first_hit()

# --- Models import (db, User) ---
MODEL_CANDIDATES = ["models", "backend.models", "srms.models", "srms_expanded.models"]
db = User = None
last_model_err = None
for m in MODEL_CANDIDATES:
    try:
        mm = importlib.import_module(m)
        if hasattr(mm, "db") and hasattr(mm, "User"):
            db = getattr(mm, "db")
            User = getattr(mm, "User")
            break
    except Exception as e:
        last_model_err = e
if db is None or User is None:
    raise ImportError(f"Could not import db/User from any of {MODEL_CANDIDATES}. Last error: {last_model_err}")

def _make_app():
    # If it's already an app instance, return it
    try:
        from flask import Flask  # type: ignore
    except Exception:
        Flask = None  # type: ignore
    if Flask is not None and not callable(_app_or_factory) and _app_or_factory.__class__.__name__ == "Flask":
        app = _app_or_factory
    else:
        # treat as factory
        if callable(_app_or_factory):
            try:
                app = _app_or_factory(testing=True)
            except TypeError:
                # factory without testing kw
                app = _app_or_factory()
        else:
            raise RuntimeError("Resolved object is neither a Flask app nor a callable factory.")
    # Minimal test config
    app.config.setdefault("TESTING", True)
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return app

@pytest.fixture
def app():
    app = _make_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        # seed admin user if not exists
        if User.query.filter_by(username="admin").first() is None:
            # Handle optional role field
            kwargs = {"username": "admin", "password_hash": generate_password_hash("password")}
            if hasattr(User, "role"):
                kwargs["role"] = "admin"
            admin = User(**kwargs)
            db.session.add(admin)
            db.session.commit()
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    # Try JSON login
    resp = client.post("/login", json={"username": "admin", "password": "password"})
    # Try form fallback
    if resp.status_code >= 400:
        resp = client.post("/login", data={"username": "admin", "password": "password"})
    data = resp.get_json(silent=True) or {}
    token = data.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}
