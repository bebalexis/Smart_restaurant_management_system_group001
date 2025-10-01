
"""
Project: Smart Restaurant Management System (SRMS)
School: University of Maryland Global Campus (UMGC)
Dept: Software Development and Security – Capstone Project
Authors: Beby Alexis, Kevin Wong, David White Jr
Date: September–October 2025

Description:
Main application entry point. Initializes Flask, database, and Socket.IO.
Registers routes and blueprints, configures security, and launches the app.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO
from werkzeug.security import check_password_hash
from datetime import datetime
from models import db, User, MenuItem, Table, Reservation, Order, OrderItem, Payment
from config import Config

# Create SocketIO once (no app yet), then bind inside factory
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")


def create_app(testing: bool = False):
    app = Flask(__name__)
    app.config.from_object(Config)

    if testing:
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    socketio.init_app(app)  # <-- bind socketio to this app

    # --------- helpers ---------
    def require_login():
        if not session.get("user_id"):
            return jsonify({"error": "login_required"}), 401

    def require_admin():
        if not session.get("user_id"):
            return jsonify({"error": "login_required"}), 401
        u = User.query.get(session["user_id"])
        if not u or getattr(u, "role", "") != "admin":
            return jsonify({"error": "admin_only"}), 403

    # --------- core routes ---------
    @app.get("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")
        data = request.form if request.form else (request.get_json(silent=True) or {})
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            return jsonify({"ok": True, "redirect": url_for("dashboard")})
        return jsonify({"ok": False, "error": "Invalid credentials"}), 401

    @app.post("/logout")
    def logout():
        session.clear()
        return jsonify({"ok": True})

    @app.get("/dashboard")
    def dashboard():
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return render_template("dashboard.html", username=session.get("username"))

    # ---------- MENU ----------
    @app.get("/api/menu")
    def list_menu():
        items = MenuItem.query.order_by(MenuItem.id.desc()).all()
        return jsonify([m.to_dict() for m in items])

    @app.post("/api/menu")
    def create_menu():
        resp = require_login()
        if resp:
            return resp
        data = request.get_json(silent=True) or {}
        m = MenuItem(
            name=data.get("name", "Item"),
            price=float(data.get("price", 0)),
            category=data.get("category", "General"),
            available=bool(data.get("available", True)),
        )
        db.session.add(m)
        db.session.commit()
        socketio.emit("event", {"type": "menu.created", "item": m.to_dict()})
        return jsonify(m.to_dict()), 201

    # ---------- TABLES ----------
    @app.get("/api/tables")
    def list_tables():
        tables = Table.query.order_by(Table.id.desc()).all()
        return jsonify([t.to_dict() for t in tables])

    @app.post("/api/tables")
    def create_table():
        resp = require_login()
        if resp:
            return resp
        data = request.get_json(silent=True) or {}
        t = Table(label=data.get("label", "T?"), capacity=int(data.get("capacity", 2)))
        db.session.add(t)
        db.session.commit()
        socketio.emit("event", {"type": "table.created", "table": t.to_dict()})
        return jsonify(t.to_dict()), 201

    # ---------- RESERVATIONS ----------
    @app.get("/api/reservations")
    def list_reservations():
        res = Reservation.query.order_by(Reservation.id.desc()).all()
        return jsonify([r.to_dict() for r in res])

    @app.post("/api/reservations")
    def create_reservation():
        resp = require_login()
        if resp:
            return resp
        data = request.get_json(silent=True) or {}
        r = Reservation(
            name=data.get("name", "Guest"),
            phone=data.get("phone", "+1"),
            size=int(data.get("size", 2)),
            time=datetime.fromisoformat(data["time"]) if data.get("time") else datetime.utcnow(),
            table_id=data.get("table_id"),
        )
        db.session.add(r)
        db.session.commit()
        socketio.emit("event", {"type": "reservation.created", "reservation": r.to_dict()})
        return jsonify(r.to_dict()), 201

    # ---------- ORDERS ----------
    @app.get("/api/orders")
    def list_orders():
        orders = Order.query.order_by(Order.id.desc()).all()
        return jsonify([o.to_dict() for o in orders])

    @app.post("/api/orders")
    def create_order():
        resp = require_login()
        if resp:
            return resp
        data = request.get_json(silent=True) or {}
        o = Order(table_id=data.get("table_id"))
        db.session.add(o)
        db.session.flush()
        for it in data.get("items", []):
            if "menu_item_id" in it:
                mi = MenuItem.query.get(it["menu_item_id"])
                if not mi:
                    continue
                oi = OrderItem(
                    order_id=o.id,
                    menu_item_id=mi.id,
                    name=mi.name,
                    price=mi.price,
                    quantity=int(it.get("quantity", 1)),
                )
            else:
                oi = OrderItem(
                    order_id=o.id,
                    menu_item_id=None,
                    name=it.get("name", "Custom"),
                    price=float(it.get("price", 0)),
                    quantity=int(it.get("quantity", 1)),
                )
            db.session.add(oi)
        db.session.commit()
        socketio.emit("event", {"type": "order.created", "order": o.to_dict()})
        return jsonify(o.to_dict()), 201

    @app.post("/api/orders/<int:order_id>/pay")
    def pay_order(order_id):
        resp = require_login()
        if resp:
            return resp
        order = Order.query.get_or_404(order_id)
        data = request.get_json(silent=True) or {}
        amount = float(data.get("amount", order.total()))
        p = Payment(order_id=order.id, amount=amount, method=data.get("method", "cash"))
        order.status = "paid" if amount >= order.total() else "partial"
        db.session.add(p)
        db.session.commit()
        socketio.emit("event", {"type": "payment.created", "order": order.to_dict(), "payment": p.to_dict()})
        return jsonify({"order": order.to_dict(), "payment": p.to_dict()})

    # ---------- REPORTS ----------
    @app.get("/api/reports/sales")
    def sales_report():
        rows = Payment.query.all()
        by_day = {}
        for p in rows:
            day = p.created_at.date().isoformat()
            by_day.setdefault(day, {"date": day, "revenue": 0.0, "payments": 0})
            by_day[day]["revenue"] += p.amount
            by_day[day]["payments"] += 1
        return jsonify(sorted(by_day.values(), key=lambda x: x["date"], reverse=True))

    # ---------- MENU UPDATE/DELETE ----------
    @app.put("/api/menu/<int:item_id>")
    def update_menu(item_id):
        resp = require_admin()
        if resp:
            return resp
        data = request.get_json(silent=True) or {}
        m = MenuItem.query.get_or_404(item_id)
        for k in ["name", "category", "available"]:
            if k in data:
                setattr(m, k, data[k])
        if "price" in data:
            m.price = float(data["price"])
        db.session.commit()
        socketio.emit("event", {"type": "menu.updated", "item": m.to_dict()})
        return jsonify(m.to_dict())

    @app.delete("/api/menu/<int:item_id>")
    def delete_menu(item_id):
        resp = require_admin()
        if resp:
            return resp
        m = MenuItem.query.get_or_404(item_id)
        db.session.delete(m)
        db.session.commit()
        socketio.emit("event", {"type": "menu.deleted", "id": item_id})
        return jsonify({"ok": True})

    # ---------- TABLES UPDATE/DELETE ----------
    @app.put("/api/tables/<int:table_id>")
    def update_table(table_id):
        resp = require_admin()
        if resp:
            return resp
        t = Table.query.get_or_404(table_id)
        data = request.get_json(silent=True) or {}
        if "label" in data:
            t.label = data["label"]
        if "capacity" in data:
            t.capacity = int(data["capacity"])
        if "occupied" in data:
            t.occupied = bool(data["occupied"])
        db.session.commit()
        socketio.emit("event", {"type": "table.updated", "table": t.to_dict()})
        return jsonify(t.to_dict())

    @app.delete("/api/tables/<int:table_id>")
    def delete_table(table_id):
        resp = require_admin()
        if resp:
            return resp
        t = Table.query.get_or_404(table_id)
        db.session.delete(t)
        db.session.commit()
        socketio.emit("event", {"type": "table.deleted", "id": table_id})
        return jsonify({"ok": True})

    # ---------- RESERVATIONS UPDATE/DELETE ----------
    @app.put("/api/reservations/<int:res_id>")
    def update_reservation(res_id):
        resp = require_login()
        if resp:
            return resp
        r = Reservation.query.get_or_404(res_id)
        data = request.get_json(silent=True) or {}
        for k in ["name", "phone"]:
            if k in data:
                setattr(r, k, data[k])
        if "size" in data:
            r.size = int(data["size"])
        if "time" in data:
            r.time = datetime.fromisoformat(data["time"]) if data["time"] else r.time
        if "table_id" in data:
            r.table_id = data["table_id"]
        db.session.commit()
        socketio.emit("event", {"type": "reservation.updated", "reservation": r.to_dict()})
        return jsonify(r.to_dict())

    @app.delete("/api/reservations/<int:res_id>")
    def delete_reservation(res_id):
        resp = require_admin()
        if resp:
            return resp
        r = Reservation.query.get_or_404(res_id)
        db.session.delete(r)
        db.session.commit()
        socketio.emit("event", {"type": "reservation.deleted", "id": res_id})
        return jsonify({"ok": True})

    # ---------- PAYMENTS LIST ----------
    @app.get("/api/payments")
    def list_payments():
        return jsonify([p.to_dict() for p in Payment.query.order_by(Payment.id.desc()).all()])

    # ---------- HEALTH ----------
    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    return app


# Create the real app object
app = create_app()

# Create tables on startup (if desired)
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    # Runs with eventlet server automatically
    socketio.run(app, host="0.0.0.0", port=5013, debug=True)