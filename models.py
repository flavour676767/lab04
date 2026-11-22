import sqlite3

from flask import current_app, g


SEED_PRODUCTS = (
    ("AWP", "Dragon Lore", "Factory New", 1249.00, "", 10),
    ("Karambit", "Doppler - Phase 2", "Factory New", 785.00, "", 10),
    ("AK-47", "Fire Serpent", "Minimal Wear", 612.00, "", 10),
)
ORDER_STATUSES = ("pending", "processing", "shipped", "completed", "cancelled")
STATUS_LABELS = {
    "pending": "Нове",
    "processing": "В обробці",
    "shipped": "Відправлено",
    "completed": "Завершено",
    "cancelled": "Скасовано",
}


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weapon TEXT NOT NULL,
            skin TEXT NOT NULL,
            quality TEXT NOT NULL,
            price REAL NOT NULL CHECK (price >= 0),
            image_url TEXT NOT NULL DEFAULT '',
            stock INTEGER NOT NULL DEFAULT 10 CHECK (stock >= 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    columns = {row["name"] for row in db.execute("PRAGMA table_info(orders)")} if db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='orders'"
    ).fetchone() else set()
    if columns and "product_id" in columns:
        db.execute("PRAGMA foreign_keys = OFF")
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute("ALTER TABLE orders RENAME TO orders_legacy")
            _create_order_tables(db)
            db.execute("""INSERT INTO orders
                (id, customer_name, customer_email, total_price, status, created_at)
                SELECT id, customer_name, customer_email, total_price, 'pending', created_at
                FROM orders_legacy""")
            db.execute("""INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity)
                SELECT id, product_id, product_name, unit_price, quantity FROM orders_legacy""")
            db.execute("DROP TABLE orders_legacy")
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.execute("PRAGMA foreign_keys = ON")
    else:
        _create_order_tables(db)
    if db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        db.executemany("INSERT INTO products (weapon, skin, quality, price, image_url, stock) VALUES (?, ?, ?, ?, ?, ?)", SEED_PRODUCTS)
    db.commit()


def _create_order_tables(db):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            total_price REAL NOT NULL CHECK (total_price >= 0),
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','processing','shipped','completed','cancelled')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            unit_price REAL NOT NULL CHECK (unit_price >= 0),
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
        );
        CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
    """)


def create_feedback(name, email, message):
    db = get_db()
    cursor = db.execute("INSERT INTO feedback (name, email, message) VALUES (?, ?, ?)", (name.strip(), email.strip(), message.strip()))
    db.commit()
    return cursor.lastrowid


def get_all_feedback():
    return get_db().execute("SELECT id, name, email, message, created_at FROM feedback ORDER BY created_at DESC, id DESC").fetchall()


def delete_feedback(feedback_id):
    db = get_db()
    cursor = db.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
    db.commit()
    return cursor.rowcount > 0


def get_products():
    return get_db().execute("SELECT id, weapon, skin, quality, price, image_url, stock FROM products ORDER BY id").fetchall()


def get_product(product_id):
    return get_db().execute("SELECT id, weapon, skin, quality, price, image_url, stock FROM products WHERE id = ?", (product_id,)).fetchone()


def save_product(product_id, weapon, skin, quality, price, image_url, stock):
    db = get_db()
    values = (weapon.strip(), skin.strip(), quality.strip(), price, image_url.strip(), stock)
    if product_id is None:
        cursor = db.execute("INSERT INTO products (weapon, skin, quality, price, image_url, stock) VALUES (?, ?, ?, ?, ?, ?)", values)
    else:
        cursor = db.execute("UPDATE products SET weapon=?, skin=?, quality=?, price=?, image_url=?, stock=? WHERE id=?", (*values, product_id))
    db.commit()
    return cursor.lastrowid if product_id is None else cursor.rowcount > 0


def delete_product(product_id):
    db = get_db()
    try:
        cursor = db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        db.rollback()
        return False


def create_order(product_id, customer_name, customer_email, quantity):
    db = get_db()
    db.execute("BEGIN IMMEDIATE")
    try:
        product = get_product(product_id)
        if product is None:
            raise ValueError("Товар не знайдено.")
        if quantity < 1:
            raise ValueError("Кількість має бути не меншою за 1.")
        if quantity > product["stock"]:
            raise ValueError("Недостатньо товару на складі.")
        total = round(product["price"] * quantity, 2)
        cursor = db.execute("INSERT INTO orders (customer_name, customer_email, total_price) VALUES (?, ?, ?)", (customer_name.strip(), customer_email.strip(), total))
        db.execute("INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity) VALUES (?, ?, ?, ?, ?)", (cursor.lastrowid, product_id, f'{product["weapon"]} | {product["skin"]}', product["price"], quantity))
        db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
        db.commit()
        return cursor.lastrowid
    except Exception:
        db.rollback()
        raise


def get_orders():
    return get_db().execute("""SELECT o.id, o.customer_name, o.customer_email, o.total_price, o.status, o.created_at,
        GROUP_CONCAT(oi.product_name || ' × ' || oi.quantity, ', ') AS items
        FROM orders o LEFT JOIN order_items oi ON oi.order_id=o.id
        GROUP BY o.id ORDER BY o.created_at DESC, o.id DESC""").fetchall()


def update_order_status(order_id, status):
    if status not in ORDER_STATUSES:
        raise ValueError("Недопустимий статус замовлення.")
    db = get_db()
    db.execute("BEGIN IMMEDIATE")
    try:
        order = db.execute("SELECT status FROM orders WHERE id=?", (order_id,)).fetchone()
        if order is None:
            db.rollback()
            return False
        old = order["status"]
        items = db.execute("SELECT product_id, quantity FROM order_items WHERE order_id=?", (order_id,)).fetchall()
        if old != "cancelled" and status == "cancelled":
            for item in items:
                db.execute("UPDATE products SET stock=stock+? WHERE id=?", (item["quantity"], item["product_id"]))
        elif old == "cancelled" and status != "cancelled":
            for item in items:
                changed = db.execute("UPDATE products SET stock=stock-? WHERE id=? AND stock>=?", (item["quantity"], item["product_id"], item["quantity"]))
                if changed.rowcount == 0:
                    raise ValueError("Недостатньо товару на складі, щоб відновити це замовлення.")
        db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
