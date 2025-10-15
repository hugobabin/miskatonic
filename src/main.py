from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from routers.etl_import import router as etl_router
from routers.login import router as login_router
from routers.question import router as questions_router
from routers.quiz import router as quizs_router
from services.log import ServiceLog
from services.mongo import ServiceMongo
from services.db_users import main as create_db


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201, ARG001
    """Handle lifespan."""
    create_db()
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

app.include_router(questions_router)
app.include_router(quizs_router)
app.include_router(login_router)
app.include_router(etl_router)


@app.get("/", tags=["root"])
async def get_root() -> ORJSONResponse:
    """Get root."""
    return ORJSONResponse(content={"message": "Miskatonic API", "status": "ok"})
