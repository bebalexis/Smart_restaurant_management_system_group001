"""
Project: Smart Restaurant Management System (SRMS)
School: UMGC – Software Development and Security
Authors: Beby Alexis, Kevin Wong, David White Jr
Date: October 2025

Description:
Contains all Flask routes for authentication, menus, tables, reservations,
orders, payments, and reports. Includes Socket.IO event handling.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="admin")

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(80), default="General")
    available = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "price": self.price, "category": self.category, "available": self.available}

class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(20), unique=True, nullable=False)
    capacity = db.Column(db.Integer, default=2)
    occupied = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {"id": self.id, "label": self.label, "capacity": self.capacity, "occupied": self.occupied}

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=True)
    table = db.relationship('Table', backref='reservations', lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "phone": self.phone, "size": self.size, "time": self.time.isoformat(), "table_id": self.table_id}

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=True)
    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', cascade="all, delete-orphan", lazy=True)
    payments = db.relationship('Payment', backref='order', cascade="all, delete-orphan", lazy=True)

    def total(self):
        return sum(oi.quantity * oi.price for oi in self.items)

    def to_dict(self):
        return {
            "id": self.id,
            "table_id": self.table_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "items": [i.to_dict() for i in self.items],
            "payments": [p.to_dict() for p in self.payments],
            "total": self.total(),
            "balance": max(0, self.total() - sum(p.amount for p in self.payments))
        }

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {"id": self.id, "order_id": self.order_id, "menu_item_id": self.menu_item_id, "name": self.name, "price": self.price, "quantity": self.quantity}

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(30), default="cash")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "order_id": self.order_id, "amount": self.amount, "method": self.method, "created_at": self.created_at.isoformat()}
