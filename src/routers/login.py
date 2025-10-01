from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import HTMLResponse
from passlib.hash import bcrypt

from services.authentification import (
    create_token,
    get_user_by_username,
    insert_auth_log,
)
from services.util import get_templates

router = APIRouter(
    prefix="/login",
)


@router.get("/", response_class=HTMLResponse, tags=["auth"])
async def get_login(request: Request) -> HTMLResponse:
    """Get login."""
    return get_templates().TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )


@router.post("/connect", tags=["auth"])
def login_connect(payload: dict = Body(...)):
    """Connect."""
    # Check required fields in the request
    username = payload.get("username")
    password = payload.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="username et password requis")

    # Look up the user in the database
    user = get_user_by_username(username)

    if not user or not bcrypt.verify(password, user[2]):  # user[2] = password_hash
        insert_auth_log(
            user[0] if user else None, username, "failed_login", "/auth/login", 401
        )
        raise HTTPException(status_code=401, detail="invalid credentials")

    if not user[3]:  # user[3] = is_active
        insert_auth_log(user[0], user[1], "login", "/auth/login", 401)
        raise HTTPException(status_code=401, detail="user inactive")

    # Generate JWT token
    tok = create_token(sub=int(user[0]), username=user[1])
    insert_auth_log(user[0], user[1], "login", "/auth/login", 200)

    # Return a basic response to the client
    return {"access_token": tok, "token_type": "bearer"}
