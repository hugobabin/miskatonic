import os

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, ORJSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.routers.login import router as login_router
from src.routers.etl_import import router as etl_router
from src.routers.question import router as questions_router
from src.routers.quiz import router as quizs_router
from src.services.log import ServiceLog
from src.services.mongo import ServiceMongo
from src.services.util import ServiceUtil, get_templates


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201, ARG001
    """Handle MongoDB connection along app's lifespan."""
    ServiceMongo.connect()
    ServiceLog.setup()
    ServiceLog.send_info("Backend started.")
    yield
    ServiceMongo.disconnect()
    ServiceLog.send_info("Backend stopped.")

app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Monitoring Prometheus
Instrumentator().instrument(app).expose(app)

#Enable CORS so that external front-ends can call this API and send cookies 
# or authorization headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware (session cookie signed by FastAPI)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
    same_site="lax",
    https_only=False,   # True en prod HTTPS
    max_age=3600
)

# Static files (CSS, JS, images)
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static"
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

# Root path
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
