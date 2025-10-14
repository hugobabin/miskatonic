from flask import Flask, render_template, request, redirect, url_for, session, send_file
import requests
from pathlib import Path

# REFACTORING MVT // Application Flask frontale qui consomme l'API FastAPI (JSON)
# REFACTORING MVT // Elle rend les templates présents dans src-client/templates
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "replace-with-secure-secret"

API_BASE = "http://localhost:8000"  # REFACTORING MVT // endpoint FastAPI


@app.before_request
def check_user_logged_in():
    # On ignore certaines routes publiques (login, static files, favicon, etc.)
    public_paths = ["/login", "/login/connect", "/static/", "/favicon.ico"]
    if any(request.path.startswith(path) for path in public_paths):
        return  # laisser passer

    # Si l'utilisateur n'est pas en session, rediriger vers login
    if not session.get("user"):
        return redirect(url_for("login"))
    return None


@app.context_processor
def inject_globals():
    # REFACTORING MVT // Injecte globalement api_base, current_year et current_user dans les templates
    return {
        "api_base": API_BASE,
        "current_year": 2025,
        "current_user": session.get("user"),
    }


def api_headers():
    # REFACTORING MVT // si connecté, envoie les headers X-User-* pour que l'API valide les roles
    headers = {}
    if session.get("user"):
        headers["x-user-id"] = str(session["user"]["id"])
        headers["x-username"] = session["user"]["username"]
    return headers


@app.route("/")
def index():
    # REFACTORING MVT // page d'accueil -> redirect to login
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login/", methods=["GET"])
def login():
    # REFACTORING MVT // affiche le formulaire de login (template existant)
    return render_template("login.html", error=None)


@app.route("/login/connect", methods=["POST"])
def login_connect():
    # REFACTORING MVT // submit du formulaire -> appel API /login/connect (JSON)
    username = request.form.get("username")
    password = request.form.get("password")
    print(username)
    print(password)
    res = requests.post(
        f"{API_BASE}/login/connect", json={"username": username, "password": password}
    )
    print(res.content)
    if res.status_code == 200:
        payload = res.json()
        if payload.get("success"):
            # store user in Flask session (frontend session)
            session["user"] = payload["user"]
            return redirect(url_for("dashboard"))
    # erreur -> réaffiche login avec message
    msg = res.json().get("message", "Identifiants invalides")
    return render_template("login.html", error=msg), 401


@app.route("/logout")
def logout():
    # REFACTORING MVT // clear session
    session.clear()
    # Optionnel: informer l'API
    try:
        requests.post(f"{API_BASE}/login/logout", headers=api_headers(), timeout=1)
    except Exception:
        pass
    return redirect(url_for("login"))


@app.route("/dashboard/")
def dashboard():
    # REFACTORING MVT // consume nothing special, renders dashboard template
    return render_template("dashboard.html", current_year=2025)


@app.route("/questions/")
def questions():
    # REFACTORING MVT // appelle l'API pour récupérer questions et les passe au template
    res = requests.get(f"{API_BASE}/questions/", headers=api_headers())
    print(res.content)
    questions = res.json().get("questions", []) if res.ok else []
    return render_template("questions.html", questions=questions)


@app.route("/quizs/")
def quizs():
    # REFACTORING MVT // appelle l'API pour récupérer quizs et les passe au template
    res = requests.get(f"{API_BASE}/quizs/", headers=api_headers())
    quizs = res.json().get("quizs", []) if res.ok else []
    return render_template("quizs.html", quizs=quizs)


@app.route("/etl/import", methods=["GET", "POST"])
def etl_import():
    # REFACTORING MVT // page upload CSV (GET) et POST -> envoie le fichier à l'API /etl/import
    if request.method == "GET":
        return render_template("etl_import.html")
    file = request.files.get("file")
    if not file:
        return render_template("etl_import.html", error="Aucun fichier"), 400
    files = {"file": (file.filename, file.stream, file.content_type)}
    res = requests.post(f"{API_BASE}/etl/import", headers=api_headers(), files=files)
    if res.ok:
        payload = res.json()
        stats = payload.get("stats")
        rapport = payload.get("file")
        rapport_url = f"{API_BASE}/etl/rapport/{rapport}" if rapport else None
        return render_template("etl_import.html", stats=stats, rapport_url=rapport_url)
    else:
        msg = res.json().get("message", "Erreur import")
        return render_template("etl_import.html", error=msg), res.status_code


if __name__ == "__main__":
    # REFACTORING MVT // lancer l'app Flask en local pour développement
    app.run(host="0.0.0.0", port=5000, debug=True)
