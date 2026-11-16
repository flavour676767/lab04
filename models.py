import sqlite3

from flask import current_app, g


<<<<<<< Updated upstream
SEED_PRODUCTS = (
    (
        "AWP",
        "Dragon Lore",
        "Factory New",
        1249.00,
        "https://community.akamai.steamstatic.com/economy/image/i0CoZ81Ui0m-9KwlBY1L_18myuGuq1wfhWSaZgMttyVfPaERSR0Wqmu7LAocGIGz3UqlXOLrxM-vMGmW8VNxu5Dx60noTyLwiYbf_jdk4veqYaF7IfysCnWRxuF4j-B-Xxa_nBovp3Pdwtj9cC_GaAd0DZdwQu9fuhS4kNy0NePntVTbjYpCyyT_3CgY5i9j_a9cBkcCWUKV",
    ),
    ("Karambit", "Doppler - Phase 2", "Factory New", 785.00, "https://cdn.cs2skins.gg/screenshots/skin-e7fd9a1907bb/fn/render.avif"),
    ("AK-47", "Fire Serpent", "Minimal Wear", 612.00, "https://cdn.cs2skins.gg/screenshots/skin-2599a8720f89/bs/render.avif"),
    ("M4A1-S", "Printstream", "Minimal Wear", 198.00, "https://cdn.cs2skins.gg/screenshots/skin-8e45a15cf7f5/bs/render.avif"),
    (
        "Butterfly Knife",
        "Fade",
        "Factory New",
        1045.00,
        "https://community.akamai.steamstatic.com/economy/image/i0CoZ81Ui0m-9KwlBY1L_18myuGuq1wfhWSaZgMttyVfPaERSR0Wqmu7LAocGIGz3UqlXOLrxM-vMGmW8VNxu5Dx60noTyL6kJ_m-B1Z-ua6bbZrLOmsD2avx-9ytd5lRi67gVNwsDvSwtqqc3iXZg4kCZYjReYLtRbum9XgYuvm5wbWjtgUzCn3iSsf8G81tFEeH9rw",
    ),
    ("USP-S", "Kill Confirmed", "Field-Tested", 87.00, "https://cdn.cs2skins.gg/screenshots/skin-cf4c11689014/bs/render.avif"),
    (
        "Glock-18",
        "Gamma Doppler",
        "Minimal Wear",
        92.00,
        "https://cdn.csgoskins.gg/public/uih/products/aHR0cHM6Ly9jZG4uY3Nnb3NraW5zLmdnL3B1YmxpYy9pbWFnZXMvYnVja2V0cy9lY29uL2RlZmF1bHRfZ2VuZXJhdGVkL3dlYXBvbl9nbG9ja19hbV9nYW1tYV9kb3BwbGVyX3BoYXNlMV9nbG9ja19saWdodC5kNzdlNjM0Mzc3NjUzMjJiYWIyNTVmNDQ3ZmY5OTcwNWU2YjZjNjIxLnBuZw--/auto/auto/85/notrim/e05d961e9b820088cdab49968a6faaef.webp",
    ),
    ("Sport Gloves", "Vice", "Field-Tested", 449.00, "https://cdn.cs2skins.gg/screenshots/skin-c1ae7186f829/bs/render.avif"),
    (
        "M4A4",
        "Howl",
        "Minimal Wear",
        899.00,
        "https://community.akamai.steamstatic.com/economy/image/i0CoZ81Ui0m-9KwlBY1L_18myuGuq1wfhWSaZgMttyVfPaERSR0Wqmu7LAocGIGz3UqlXOLrxM-vMGmW8VNxu5Dx60noTyL8ypexwiFO0P_6afVSKP-EAm6extF6ueZhW2exwkl2tmTXwt39eCiUPQR2DMN4TOVetUK8xoLgM-K341eM2otDnC6okGoXufBz_TAB",
    ),
    ("Desert Eagle", "Blaze", "Factory New", 134.00, "https://cdn.cs2skins.gg/screenshots/skin-e30d23329629/fn/render.avif"),
    (
        "Butterfly Knife",
        "Marble Fade",
        "Factory New",
        918.00,
        "https://community.akamai.steamstatic.com/economy/image/i0CoZ81Ui0m-9KwlBY1L_18myuGuq1wfhWSaZgMttyVfPaERSR0Wqmu7LAocGIGz3UqlXOLrxM-vMGmW8VNxu5Dx60noTyL6kJ_m-B1Z-ua6bbZrLOmsD2qvzO9ksu1scC-ykRgYvzSCkpu3JCrBPVMkCZIiFLUC40S-l9DkZerg4Qfc3Y9DzCuo3SlK6ydv5e9UA71lpPNwsjHPzA",
    ),
    ("Driver Gloves", "King Snake", "Field-Tested", 288.00, "https://cdn.cs2skins.gg/screenshots/skin-ead101bfb2c9/bs/render.avif"),
)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
=======
def get_db():
    """Return the SQLite connection for the current application context."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
>>>>>>> Stashed changes
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
<<<<<<< Updated upstream


def init_db():
    db = get_db()
    db.executescript(
        """
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

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            unit_price REAL NOT NULL CHECK (unit_price >= 0),
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            total_price REAL NOT NULL CHECK (total_price >= 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE RESTRICT
        );
        """
    )
    product_count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if product_count == 0:
        db.executemany(
            """
            INSERT INTO products (weapon, skin, quality, price, image_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            SEED_PRODUCTS,
        )
    db.commit()


def create_feedback(name, email, message):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO feedback (name, email, message) VALUES (?, ?, ?)",
        (name.strip(), email.strip(), message.strip()),
    )
    db.commit()
    return cursor.lastrowid


def get_all_feedback():
    return get_db().execute(
        "SELECT id, name, email, message, created_at "
        "FROM feedback ORDER BY created_at DESC, id DESC"
    ).fetchall()


def get_feedback(feedback_id):
    return get_db().execute(
        "SELECT id, name, email, message, created_at "
        "FROM feedback WHERE id = ?",
        (feedback_id,),
    ).fetchone()


def update_feedback(feedback_id, name, email, message):
    db = get_db()
    cursor = db.execute(
        "UPDATE feedback SET name = ?, email = ?, message = ? WHERE id = ?",
        (name.strip(), email.strip(), message.strip(), feedback_id),
    )
    db.commit()
    return cursor.rowcount > 0


def delete_feedback(feedback_id):
    db = get_db()
    cursor = db.execute(
        "DELETE FROM feedback WHERE id = ?",
        (feedback_id,),
    )
    db.commit()
    return cursor.rowcount > 0


def get_products():
    return get_db().execute(
        "SELECT id, weapon, skin, quality, price, image_url, stock "
        "FROM products ORDER BY id"
    ).fetchall()


def get_product(product_id):
    return get_db().execute(
        "SELECT id, weapon, skin, quality, price, image_url, stock "
        "FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()


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

        unit_price = product["price"]
        total_price = round(unit_price * quantity, 2)
        cursor = db.execute(
            """
            INSERT INTO orders (
                product_id, product_name, unit_price, quantity,
                customer_name, customer_email, total_price
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                f'{product["weapon"]} | {product["skin"]}',
                unit_price,
                quantity,
                customer_name.strip(),
                customer_email.strip(),
                total_price,
            ),
        )
        db.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (quantity, product_id),
        )
        db.commit()
        return cursor.lastrowid
    except Exception:
        db.rollback()
        raise
=======
>>>>>>> Stashed changes
