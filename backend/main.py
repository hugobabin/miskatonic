from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from services.mongo import ServiceMongo
from services.quiz import ServiceQuiz
from models.quiz import Quiz


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201, ARG001
    """Handle MongoDB connection along app's lifespan."""
    ServiceMongo.connect()
    yield
    ServiceMongo.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/hello")
async def root() -> PlainTextResponse:
    """Hello World."""
    return PlainTextResponse("Hello!")


@app.get("/quiz/generate")
async def generate_quiz() -> None:
    ServiceQuiz.generate(
        total_questions=2,
    )
