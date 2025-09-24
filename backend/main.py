import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from backend.models.question import QuestionGetter, QuestionModel
from backend.models.quiz import QuizGenerator, QuizModel
from prometheus_fastapi_instrumentator import Instrumentator
from backend.services.log import ServiceLog
from backend.services.mongo import ServiceMongo
from backend.services.question import ServiceQuestion
from backend.services.quiz import ServiceQuiz
from backend.services.authentification import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201, ARG001
    """Handle MongoDB connection along app's lifespan."""
    ServiceMongo.connect()
    ServiceLog.setup()
    ServiceLog.send("Backup started.")
    yield
    ServiceMongo.disconnect()
    ServiceLog.send("Backup stopped.")


app = FastAPI(lifespan=lifespan)

Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    """Handle all exceptions."""
    ServiceLog.send(f"{request.url.path} -> 500")
    return ORJSONResponse(
        content={"detail": str(exc)},
        status_code=500,
    )


def handle_request_success(
    request: Request,
    data: Any = None,  # noqa: ANN401
    message: str | None = None,  # noqa: FA102
    status_code: int = 201,
) -> ORJSONResponse:
    """Standardize successful responses with logging."""
    ServiceLog.send(f"{request.url.path} -> {status_code}")
    return ORJSONResponse(
        content=data if data is not None else {"message": message},
        status_code=status_code,
    )


@app.post("/quiz/generate")
async def generate_quiz(params: QuizGenerator, request: Request) -> None:
    """Generate a quiz."""
    ServiceQuiz.generate(
        total_questions=params.total_questions,
        subjects=params.subjects,
        use=params.use,
    )
    return handle_request_success(
        request=request,
        message="Successfully generated a quiz.",
    )


@app.get("/quiz/get_all")
async def get_all_quizs(request: Request) -> ORJSONResponse:
    """Get all quizs from MongoDB."""
    quizs = ServiceQuiz.list_all()
    quizs = [quiz.model_dump() for quiz in quizs]
    return handle_request_success(request=request, data=quizs)


@app.post("/quiz/archive")
async def archive_quiz(quiz_id: str, request: Request) -> ORJSONResponse:
    """Archive a quiz in MongoDB."""
    ServiceQuiz.archive(quiz_id=quiz_id)
    return handle_request_success(
        request=request,
        message=f"Successfully archived quiz with id {quiz_id}",
    )


@app.post("/question/create")
async def create_question(question: QuestionModel, request: Request) -> ORJSONResponse:
    """Create question in MongoDB based on POST body."""
    ServiceQuestion.create(question=question)
    return handle_request_success(
        request=request,
        message="Succesfully created question.",
    )


@app.post("/question/create_bulk")
async def create_questions(
    questions: list[QuestionModel],
    request: Request,
) -> ORJSONResponse:
    """Create questions in MongoDB based on POST body."""
    ServiceQuestion.create_all(questions=questions)
    return handle_request_success(
        request=request,
        message="Successfully created questions.",
    )


@app.get("/question/get_all")
async def get_all_questions(request: Request) -> ORJSONResponse:
    """Get all questions from MongoDB."""
    questions = ServiceQuestion.list_all()
    questions = [question.model_dump() for question in questions]
    return handle_request_success(request=request, data=questions)


@app.post("/question/get_some")
async def get_some_questions(
    params: QuestionGetter,
    request: Request,
) -> ORJSONResponse:
    """Get some questions from MongoDB."""
    questions = ServiceQuestion.list_some(subjects=params.subjects, use=params.use)
    questions = [question.model_dump() for question in questions]
    return handle_request_success(request=request, data=questions)


@app.post("/question/archive")
async def archive_question(question_id: str, request: Request) -> ORJSONResponse:
    """Archive a question in MongoDB."""
    ServiceQuestion.archive(question_id=question_id)
    return handle_request_success(
        request=request,
        message=f"Successfully archived question with id {question_id}",
    )


@app.post("/question/edit")
async def edit_question(
    question_id: str, question: QuestionModel, request: Request
) -> ORJSONResponse:
    """Edit a question in MongoDB."""
    ServiceQuestion.edit(question_id=question_id, question=question)
    return handle_request_success(
        request=request,
        message=f"Successfully edited question with id {question_id}",
    )

app.include_router(auth_router) 