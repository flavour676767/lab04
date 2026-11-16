import sqlite3
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
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
