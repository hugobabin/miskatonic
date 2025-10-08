# src/services/authentification.py
import sqlite3

from pathlib import Path

# ------ Config --------
ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "bdd" / "quiz_users.sqlite"


# --- Connexion DB ---
def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


# --- Util DB ---
def get_user_by_username(username) -> tuple | None:
    with connect() as c:
        cur = c.execute("SELECT * FROM users WHERE username=?", (username,))
        return cur.fetchone()


def get_user_by_id(uid):
    with connect() as c:
        cur = c.execute("SELECT * FROM users WHERE id=?", (uid,))
        return cur.fetchone()


def get_roles_for_user(uid):
    sql = """
    SELECT r.name FROM roles r
    JOIN user_role ur ON ur.role_id = r.id
    WHERE ur.user_id = ?
    """
    with connect() as c:
        return {row[0] for row in c.execute(sql, (uid,))}


def insert_auth_log(user_id, username, action, route, status_code):
    with connect() as c:
        c.execute(
            """INSERT INTO auth_log(user_id, username, action, route, status_code)
                     VALUES (?,?,?,?,?)""",
            (user_id, username, action, route, status_code),
        )
        c.commit()
