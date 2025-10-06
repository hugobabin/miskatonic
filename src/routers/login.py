from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from passlib.hash import bcrypt
from src.services.authentification import get_user_by_username, insert_auth_log
from src.services.util import get_templates

# Create a router for login-related endpoints
router = APIRouter(prefix="/login")

# Display the login page
@router.get("/", response_class=HTMLResponse, tags=["auth"])
def get_login(request: Request) -> HTMLResponse:
    return get_templates().TemplateResponse("login.html", {"request": request})

# Handle login form submission
@router.post("/connect", tags=["auth"], name="login_connect")
def login_connect(
    request: Request, 
    username: str = Form(...),
    password: str = Form(...)):

    # Retrieve user from database
    user = get_user_by_username(username)

    # Check if user exists and password is correct
    if not user or not bcrypt.verify(password, user[2]):
        # Log failed login attempt
        insert_auth_log(user[0] if user else None, username, "failed_login", "/login/connect", 401)
        # Return login page with error
        return get_templates().TemplateResponse(
            "login.html",
            {"request": request, "error": "Identifiants invalides"},status_code=401
        )
    # Check if user is active
    if not user[3]:
        insert_auth_log(user[0], user[1], "login", "/login/connect", 401)
        return get_templates().TemplateResponse(
            "login.html",
            {"request": request, "error": "Utilisateur inactif"},status_code=401
        )
    
    # Store user info in session
    request.session["user"]={"id":int(user[0]),"username":user[1]}
    # Log successful login
    insert_auth_log(user[0], user[1], "login", "/auth/login", 200)
    # Redirect to menu page
    return RedirectResponse(url="/login/menu", status_code=303)

# Display the menu page after login
@router.get("/menu", response_class=HTMLResponse, tags=["auth"])
def menu(request: Request):
    return get_templates().TemplateResponse("menu.html", {"request": request})

# Handle logout and clear session
@router.post("/logout", tags=["auth"])
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)