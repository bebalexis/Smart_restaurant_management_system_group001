from werkzeug.security import generate_password_hash
from models import db, User, MenuItem, Table
from app import create_app

app = create_app()
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password_hash=generate_password_hash("password"), role="admin")
        db.session.add(admin)

    if MenuItem.query.count() == 0:
        items = [
            MenuItem(name="Margherita Pizza", price=11.99, category="Pizza"),
            MenuItem(name="Caesar Salad", price=9.50, category="Salad"),
            MenuItem(name="Spaghetti Bolognese", price=12.25, category="Pasta"),
        ]
        db.session.add_all(items)

    if Table.query.count() == 0:
        db.session.add_all([Table(label="T1", capacity=4), Table(label="T2", capacity=2), Table(label="T3", capacity=6)])

    db.session.commit()
    print("Seeded. Username=admin, Password=password")
