import os
from contextlib import asynccontextmanager

import arel
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, ORJSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware

from routers.etl_import import router as etl_router
from routers.login import get_login
from routers.login import router as login_router
from routers.question import router as questions_router
from routers.quiz import router as quizs_router
from services.log import ServiceLog
from services.mongo import ServiceMongo
from services.util import ServiceUtil, get_templates


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201, ARG001
    """Handle MongoDB connection along app's lifespan."""
    ServiceMongo.connect()
    ServiceLog.setup()
    ServiceLog.send_info("Backend started.")
    yield
    ServiceMongo.disconnect()
    ServiceLog.send_info("Backend stopped.")


app = FastAPI(lifespan=lifespan)

Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(questions_router)
app.include_router(quizs_router)
app.include_router(login_router)
app.include_router(etl_router)

if _debug := ServiceUtil.get_env("DEBUG"):
    hot_reload = arel.HotReload(paths=[arel.Path(".")])
    app.add_websocket_route("/hot-reload", route=hot_reload, name="hot-reload")
    app.add_event_handler("startup", hot_reload.startup)
    app.add_event_handler("shutdown", hot_reload.shutdown)
    get_templates().env.globals["DEBUG"] = _debug
    get_templates().env.globals["hot_reload"] = hot_reload


@app.middleware("http")
async def check_auth(request: Request, call_next):
    """Protect routes behind authentification middleware."""
    if request.url.path.startswith("/login") or request.url.path.startswith("/static"):
        return await call_next(request)
    # if not logged on
    if True:
        return await get_login(request)
    # if logged
    return await call_next(request)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    """Handle all exceptions."""
    print("pretty please...")


app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
    same_site="lax",
    https_only=False,  # True en prod HTTPS
    max_age=3600,
)

# Include all routers
app.include_router(questions_router)
app.include_router(quizs_router)
app.include_router(login_router)
app.include_router(etl_router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    ServiceLog.send_info("Tu devrais log une erreur non ?")
    return ORJSONResponse(
        content={"detail": str(exc)},
        status_code=500,
    )


@app.get("/", response_class=HTMLResponse, tags=["root"])
async def get_root(request: Request) -> HTMLResponse:
    """Get root."""
    return get_templates().TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


# Catch-all route to serve the login page for any other path (except /docs, /redoc, /openapi.json)
@app.get("/{rest_of_path:path}", tags=["others"])
async def catch_other_paths(request: Request, rest_of_path: str) -> HTMLResponse:
    if rest_of_path in ["docs", "redoc", "openapi.json"]:
        return RedirectResponse(url=f"/{rest_of_path}")
    return get_templates().TemplateResponse("login.html", {"request": request})
