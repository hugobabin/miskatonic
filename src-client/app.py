import contextlib
import os

import requests
from dotenv import load_dotenv
from fastapi.responses import FileResponse
from flask import (
    Flask,
    Response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

app = Flask(__name__, template_folder="templates", static_folder="static")

load_dotenv("../.env")
app.secret_key = os.getenv("SECRET_KEY")

API_BASE = "http://localhost:8000"


@app.before_request
def check_user_logged_in() -> Response | None:
    """Check if user is logged in."""
    public_paths = ["/login", "/login/connect", "/static/", "/favicon.ico"]
    if any(request.path.startswith(path) for path in public_paths):
        return None
    if not session.get("user"):
        return redirect(url_for("login"))
    return None


@app.context_processor
def inject_globals() -> dict:
    """Inject globals."""
    return {
        "api_base": API_BASE,
        "current_year": 2025,
        "current_user": session.get("user"),
    }


def api_headers() -> dict:
    """Get headers."""
    headers = {}
    if session.get("user"):
        headers["x-user-id"] = str(session["user"]["id"])
        headers["x-username"] = session["user"]["username"]
    return headers


@app.route("/")
def index() -> Response:
    """Get index."""
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login/", methods=["GET"])
def login() -> str:
    """Get login."""
    return render_template("login.html", error=None)


@app.route("/login/connect", methods=["POST"])
def login_connect() -> Response | None:
    """Connect."""
    username = request.form.get("username")
    password = request.form.get("password")
    res = requests.post(
        f"{API_BASE}/login/connect", json={"username": username, "password": password}
    )
    if res.status_code == 200:
        payload = res.json()
        if payload.get("success"):
            session["user"] = payload["user"]
            return redirect(url_for("dashboard"))
    msg = res.json().get("message", "Identifiants invalides")
    return render_template("login.html", error=msg), 401


@app.route("/logout")
def logout() -> Response:
    """Disconnect."""
    session.clear()
    with contextlib.suppress(Exception):
        requests.post(f"{API_BASE}/login/logout", headers=api_headers(), timeout=1)
    return redirect(url_for("login"))


@app.route("/dashboard/")
def dashboard() -> str:
    """Get dashboard."""
    return render_template("dashboard.html", current_year=2025)


@app.route("/questions/")
def questions() -> str:
    """Get questions."""
    res = requests.get(f"{API_BASE}/questions/", headers=api_headers())
    questions = res.json().get("questions", []) if res.ok else []
    return render_template("questions.html", questions=questions)


@app.route("/quizs/")
def quizs() -> str:
    """Get quizs."""
    res = requests.get(f"{API_BASE}/quizs/", headers=api_headers())
    quizs = res.json().get("quizs", []) if res.ok else []
    return render_template("quizs.html", quizs=quizs)


@app.route("/etl/import", methods=["GET", "POST"])
def etl_import() -> str:
    """Import CSV."""
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
        return render_template("etl_import.html", stats=stats, rapport=rapport)
    msg = res.json().get("message", "Erreur import")
    return render_template("etl_import.html", error=msg), res.status_code


@app.route("/etl/rapport/<rapport>")
def etl_import_get_rapport(rapport):
    """Get rapport."""
    res: FileResponse = requests.get(
        f"{API_BASE}/etl/rapport/{rapport}", headers=api_headers()
    )
    if res.status_code == 200:
        response = Response(
            res.content,
            content_type="test/csv",
        )
        response.headers["Content-Disposition"] = f"attachment; filename={rapport}"
        return response
    return (
        render_template("etl_import.html", errorr="Erreur durant ouverture du rapport"),
        res.status_code,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
