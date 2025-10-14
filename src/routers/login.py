# ...existing code...
from fastapi import APIRouter, Request, Form, Body
from fastapi.responses import ORJSONResponse
from passlib.hash import bcrypt
from services.authentification import get_user_by_username, insert_auth_log

router = APIRouter(prefix="/login")


@router.post("/connect", tags=["auth"], name="login_connect")
async def login_connect(request: Request, body: dict = Body(...)) -> ORJSONResponse:
    # REFACTORING MVT // Endpoint API : renvoie JSON indiquant succès / erreur.
    # Support JSON body: {"username": "...", "password": "..."}
    username = body.get("username")
    password = body.get("password")
    print(username)
    print(password)

    user = get_user_by_username(username)
    if not user or not bcrypt.verify(password or "", user[2]):
        insert_auth_log(
            user[0] if user else None, username, "failed_login", "/login/connect", 401
        )
        return ORJSONResponse(
            content={"success": False, "message": "Identifiants invalides"},
            status_code=401,
        )

    if not user[3]:
        insert_auth_log(user[0], user[1], "login_inactive", "/login/connect", 401)
        return ORJSONResponse(
            content={"success": False, "message": "Utilisateur inactif"},
            status_code=401,
        )

    # REFACTORING MVT // On renvoie l'objet user au frontend; c'est au frontend (Flask) de stocker la session.
    insert_auth_log(user[0], user[1], "login", "/login/connect", 200)
    return ORJSONResponse(
        content={"success": True, "user": {"id": int(user[0]), "username": user[1]}}
    )


@router.post("/logout", tags=["auth"], name="logout")
async def logout(request: Request) -> ORJSONResponse:
    # REFACTORING MVT // API de logout : stateless ici, retourne juste confirmation
    return ORJSONResponse(content={"success": True, "message": "Logged out"})


# ...existing code...
