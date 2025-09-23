# auth_api.py
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import jwt
from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.hash import bcrypt

# --- Config ---
ROOT = Path(__file__).resolve().parents[2] 
DB_PATH = ROOT / "bdd" / "quiz_users.sqlite"
SECRET = "change-me"                            # mets une vraie clé
ALGO = "HS256"
ACCESS_MIN = 60

# --- Util DB ---
def connect() :
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def get_user_by_username(username):
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
        return {row["name"] for row in c.execute(sql, (uid,))}

def insert_auth_log(user_id, username, action, route, status_code):
    with connect() as c:
        c.execute("""INSERT INTO auth_log(user_id, username, action, route, status_code)
                     VALUES (?,?,?,?,?)""", (user_id, username, action, route, status_code))
        c.commit()

# --- Sécurité ---
def create_token(sub, username = None, role = None):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_MIN)).timestamp()),
    }
    if username:
        payload["username"] = username
    if role:
        payload["role"] = role
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def decode_token(token):
    return jwt.decode(token, SECRET, algorithms=[ALGO])

bearer = HTTPBearer(auto_error=True)
def get_current_user(cred: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        payload = decode_token(cred.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = get_user_by_id(int(sub))
    if not user or not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user

def require_roles(*allowed):
    def checker(user: sqlite3.Row = Depends(get_current_user)):
        roles = get_roles_for_user(int(user["id"]))
        if roles.isdisjoint(set(allowed)):
            raise HTTPException(status_code=403)
        return user
    return checker

# --- API ---

class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

app = FastAPI(title="Quiz Auth API")

@app.post("/auth/login", response_model=TokenOut, tags=["auth"])
def login(payload: LoginIn, request: Request):
    u = get_user_by_username(payload.username)
    if not u or not bcrypt.verify(payload.password, u["password_hash"]):
        insert_auth_log(u["id"] if u else None, payload.username, "failed_login", "/auth/login", 401)
        raise HTTPException(status_code=401, detail="invalid credentials")
    if not u["is_active"]:
        insert_auth_log(u["id"], u["username"], "login", "/auth/login", 401)
        raise HTTPException(status_code=401, detail="user inactive")
    tok = create_token(sub=int(u["id"]))
    insert_auth_log(u["id"], u["username"], "login", "/auth/login", 200)
    return TokenOut(access_token=tok)
