from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from routers.login import router as login_router
from routers.question import router as questions_router
from routers.quiz import router as quizs_router
from services.log import ServiceLog
from services.mongo import ServiceMongo
from services.util import get_templates


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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    """Handle all exceptions."""
    print("pretty please...")
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


@app.get("/{rest_of_path:path}", tags=["others"])
async def catch_other_paths(request: Request, rest_of_path: str) -> HTMLResponse:
    """Catch other paths."""
    return get_templates().TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )
