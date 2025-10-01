# backend/services/authentification.py
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import APIRouter, HTTPException, status, Depends, Body 
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.hash import bcrypt
import os
from dotenv import load_dotenv

# ------ Config --------
ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "bdd" / "quiz_users.sqlite"
load_dotenv()
# Secret key used to sign and verify JWT tokens
SECRET = os.getenv("SECRET_KEY")
# Algorithm used to decode and verify JWT tokens
ALGO = "HS256"
ACCESS_MIN = 60
# Reusable HTTPBearer instance to extract the token from requests
bearer = HTTPBearer(auto_error=True)

router = APIRouter(prefix="/auth", tags=["auth"]) 

# --- Connexion DB ---
def connect()-> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

# --- Util DB ---
def get_user_by_username(username)-> tuple | None:
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
        c.execute("""INSERT INTO auth_log(user_id, username, action, route, status_code)
                     VALUES (?,?,?,?,?)""", (user_id, username, action, route, status_code))
        c.commit()

# --- JWT ---
def create_token(sub, username=None, role=None):
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

# --- Dependencies ---
def get_current_user(cred: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        payload = decode_token(cred.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = get_user_by_id(int(sub))
    if not user or not user[3]:   # colonne is_active
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user

def require_teacher(user = Depends(get_current_user)):
    roles = get_roles_for_user(int(user[0]))
    if "teacher" not in roles:
        raise HTTPException(status_code=403)
    return user

def require_admin(user = Depends(get_current_user)):
    roles = get_roles_for_user(int(user[0]))
    if "admin" not in roles:
        raise HTTPException(status_code=403)
    return user

# --- API ---

@router.post("/login")
def login(payload: dict = Body(...)):  
   # Check required fields in the request
    username = payload.get("username")
    password = payload.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="username et password requis")

    # Look up the user in the database
    user = get_user_by_username(username)

    if not user or not bcrypt.verify(password, user[2]):  # user[2] = password_hash
        insert_auth_log(user[0] if user else None, username, "failed_login", "/auth/login", 401)
        raise HTTPException(status_code=401, detail="invalid credentials")

    if not user[3]:  # user[3] = is_active
        insert_auth_log(user[0], user[1], "login", "/auth/login", 401)
        raise HTTPException(status_code=401, detail="user inactive")

    # Generate JWT token
    tok = create_token(sub=int(user[0]), username=user[1])
    insert_auth_log(user[0], user[1], "login", "/auth/login", 200)

    # Return a basic response to the client
    return {
        "access_token": tok,
        "token_type": "bearer"
    }