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
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    orders_exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='orders'").fetchone()
    if not orders_exists:
        _create_order_tables(db)
    else:
        columns = {row["name"] for row in db.execute("PRAGMA table_info(orders)")}
        if "product_id" in columns:
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
            if "user_id" not in columns:
                db.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE")
            db.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)")

    if db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        db.executemany("INSERT INTO products (weapon, skin, quality, price, image_url, stock) VALUES (?, ?, ?, ?, ?, ?)", SEED_PRODUCTS)

    # Seed users and initial orders if users is empty
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        seed_users = (
            ("Влад Завиднюк", "skebob@gmail.com"),
            ("Давид Біскій", "bis.david11@gmail.com"),
            ("Ілля Прадійчук", "pradiychuk@example.com"),
        )
        user_ids = []
        for uname, uemail in seed_users:
            c = db.execute("INSERT INTO users (name, email) VALUES (?, ?)", (uname, uemail))
            user_ids.append(c.lastrowid)

        # Seed initial orders for them if orders is empty
        if db.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
            db_products = db.execute("SELECT id, weapon, skin, price, stock FROM products ORDER BY id").fetchall()
            if len(db_products) >= 3:
                sample_orders_data = [
                    (user_ids[0], seed_users[0][0], seed_users[0][1], db_products[0], "completed"),
                    (user_ids[1], seed_users[1][0], seed_users[1][1], db_products[1], "processing"),
                    (user_ids[2], seed_users[2][0], seed_users[2][1], db_products[2], "pending"),
                ]
                for uid, cname, cemail, prod, st in sample_orders_data:
                    c_ord = db.execute(
                        "INSERT INTO orders (user_id, customer_name, customer_email, total_price, status) VALUES (?, ?, ?, ?, ?)",
                        (uid, cname, cemail, prod["price"], st)
                    )
                    oid = c_ord.lastrowid
                    db.execute(
                        "INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity) VALUES (?, ?, ?, ?, 1)",
                        (oid, prod["id"], f"{prod['weapon']} | {prod['skin']}", prod["price"])
                    )

    # Backfill any existing orphan orders to link to users
    unlinked = db.execute("SELECT id, customer_name, customer_email FROM orders WHERE user_id IS NULL").fetchall()
    for row in unlinked:
        u = db.execute("SELECT id FROM users WHERE email = ?", (row["customer_email"],)).fetchone()
        if not u:
            c = db.execute("INSERT INTO users (name, email) VALUES (?, ?)", (row["customer_name"], row["customer_email"]))
            uid = c.lastrowid
        else:
            uid = u["id"]
        db.execute("UPDATE orders SET user_id = ? WHERE id = ?", (uid, row["id"]))

    db.commit()


def _create_order_tables(db):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            total_price REAL NOT NULL CHECK (total_price >= 0),
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','processing','shipped','completed','cancelled')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
        CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
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


def get_users():
    db = get_db()
    users = db.execute("SELECT id, name, email, created_at FROM users ORDER BY id").fetchall()
    result = []
    for u in users:
        orders = get_user_orders(u["id"])
        result.append({
            "id": u["id"],
            "name": u["name"],
            "email": u["email"],
            "created_at": u["created_at"],
            "orders": orders,
            "orders_count": len(orders),
            "total_spent": sum(o["total_price"] for o in orders if o["status"] != "cancelled"),
        })
    return result


def get_user(user_id):
    db = get_db()
    u = db.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    if u is None:
        return None
    user = dict(u)
    user["orders"] = get_user_orders(user_id)
    return user


def save_user(user_id, name, email):
    db = get_db()
    name = name.strip()
    email = email.strip()
    if not name or not email or "@" not in email:
        raise ValueError("Вкажіть коректне ім’я та адресу електронної пошти.")

    if user_id is None:
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise ValueError(f"Користувач із поштою {email} вже існує.")
        cursor = db.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
        db.commit()
        return cursor.lastrowid
    else:
        existing = db.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id)).fetchone()
        if existing:
            raise ValueError(f"Електронна пошта {email} вже використовується іншим користувачем.")
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute("UPDATE users SET name = ?, email = ? WHERE id = ?", (name, email, user_id))
            db.execute("UPDATE orders SET customer_name = ?, customer_email = ? WHERE user_id = ?", (name, email, user_id))
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise


def delete_user(user_id):
    db = get_db()
    db.execute("BEGIN IMMEDIATE")
    try:
        user = db.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if user is None:
            db.rollback()
            return False
        orders = db.execute("SELECT id, status FROM orders WHERE user_id = ?", (user_id,)).fetchall()
        for o in orders:
            if o["status"] != "cancelled":
                items = db.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (o["id"],)).fetchall()
                for it in items:
                    db.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (it["quantity"], it["product_id"]))
            db.execute("DELETE FROM order_items WHERE order_id = ?", (o["id"],))
        db.execute("DELETE FROM orders WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def get_user_orders(user_id):
    db = get_db()
    rows = db.execute("""
        SELECT o.id, o.user_id, o.customer_name, o.customer_email, o.total_price, o.status, o.created_at
        FROM orders o
        WHERE o.user_id = ?
        ORDER BY o.created_at DESC, o.id DESC
    """, (user_id,)).fetchall()
    orders = []
    for r in rows:
        order = dict(r)
        items = db.execute("""
            SELECT oi.id, oi.product_id, oi.product_name, oi.unit_price, oi.quantity,
                   p.weapon, p.skin
            FROM order_items oi
            LEFT JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
        """, (order["id"],)).fetchall()
        order["items_list"] = [dict(it) for it in items]
        order["items_text"] = ", ".join(f"{it['product_name']} × {it['quantity']}" for it in items) if items else "—"
        orders.append(order)
    return orders


def create_order(product_id, customer_name, customer_email, quantity, user_id=None, status="pending"):
    if status not in ORDER_STATUSES:
        raise ValueError("Недопустимий статус замовлення.")
    db = get_db()
    db.execute("BEGIN IMMEDIATE")
    try:
        product = get_product(product_id)
        if product is None:
            raise ValueError("Товар не знайдено.")
        if quantity < 1:
            raise ValueError("Кількість має бути не меншою за 1.")
        if status != "cancelled" and quantity > product["stock"]:
            raise ValueError("Недостатньо товару на складі.")

        if user_id is not None:
            user = db.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
            if user:
                customer_name = user["name"]
                customer_email = user["email"]
        else:
            customer_email = customer_email.strip()
            customer_name = customer_name.strip()
            user = db.execute("SELECT id, name, email FROM users WHERE email = ?", (customer_email,)).fetchone()
            if user is None:
                cur_u = db.execute("INSERT INTO users (name, email) VALUES (?, ?)", (customer_name, customer_email))
                user_id = cur_u.lastrowid
            else:
                user_id = user["id"]

        total = round(product["price"] * quantity, 2)
        cursor = db.execute(
            "INSERT INTO orders (user_id, customer_name, customer_email, total_price, status) VALUES (?, ?, ?, ?, ?)",
            (user_id, customer_name.strip(), customer_email.strip(), total, status)
        )
        order_id = cursor.lastrowid
        db.execute(
            "INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity) VALUES (?, ?, ?, ?, ?)",
            (order_id, product_id, f'{product["weapon"]} | {product["skin"]}', product["price"], quantity)
        )
        if status != "cancelled":
            db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
        db.commit()
        return order_id
    except Exception:
        db.rollback()
        raise


def update_order(order_id, product_id=None, quantity=None, total_price=None, status=None, user_id=None):
    db = get_db()
    db.execute("BEGIN IMMEDIATE")
    try:
        order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if order is None:
            raise ValueError("Замовлення не знайдено.")

        old_status = order["status"]
        new_status = status if status in ORDER_STATUSES else old_status

        current_item = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchone()

        if product_id is not None and quantity is not None:
            quantity = int(quantity)
            if quantity < 1:
                raise ValueError("Кількість має бути не меншою за 1.")
            product = get_product(product_id)
            if product is None:
                raise ValueError("Товар не знайдено.")

            # Restore old stock if old_status was active
            if current_item and old_status != "cancelled":
                db.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (current_item["quantity"], current_item["product_id"]))

            # Deduct new stock if new_status is active
            if new_status != "cancelled":
                cur_stock = db.execute("SELECT stock FROM products WHERE id = ?", (product_id,)).fetchone()["stock"]
                if cur_stock < quantity:
                    raise ValueError(f"Недостатньо товару на складі (залишок: {cur_stock}).")
                db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))

            if current_item:
                db.execute("""
                    UPDATE order_items
                    SET product_id = ?, product_name = ?, unit_price = ?, quantity = ?
                    WHERE id = ?
                """, (product_id, f"{product['weapon']} | {product['skin']}", product["price"], quantity, current_item["id"]))
            else:
                db.execute("""
                    INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity)
                    VALUES (?, ?, ?, ?, ?)
                """, (order_id, product_id, f"{product['weapon']} | {product['skin']}", product["price"], quantity))

            if total_price is None or total_price < 0:
                total_price = round(product["price"] * quantity, 2)
        else:
            if old_status != "cancelled" and new_status == "cancelled":
                items = db.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
                for item in items:
                    db.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (item["quantity"], item["product_id"]))
            elif old_status == "cancelled" and new_status != "cancelled":
                items = db.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
                for item in items:
                    changed = db.execute("UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?", (item["quantity"], item["product_id"], item["quantity"]))
                    if changed.rowcount == 0:
                        raise ValueError("Недостатньо товару на складі, щоб відновити це замовлення.")

        if total_price is None:
            total_price = order["total_price"]

        target_user_id = user_id if user_id is not None else order["user_id"]
        if target_user_id:
            u = db.execute("SELECT name, email FROM users WHERE id = ?", (target_user_id,)).fetchone()
            if u:
                c_name = u["name"]
                c_email = u["email"]
            else:
                c_name = order["customer_name"]
                c_email = order["customer_email"]
        else:
            c_name = order["customer_name"]
            c_email = order["customer_email"]

        db.execute("""
            UPDATE orders
            SET user_id = ?, customer_name = ?, customer_email = ?, total_price = ?, status = ?
            WHERE id = ?
        """, (target_user_id, c_name, c_email, total_price, new_status, order_id))

        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def delete_order(order_id):
    db = get_db()
    db.execute("BEGIN IMMEDIATE")
    try:
        order = db.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
        if order is None:
            db.rollback()
            return False
        if order["status"] != "cancelled":
            items = db.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
            for item in items:
                db.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (item["quantity"], item["product_id"]))
        db.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def get_orders():
    return get_db().execute("""SELECT o.id, o.user_id, o.customer_name, o.customer_email, o.total_price, o.status, o.created_at,
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
