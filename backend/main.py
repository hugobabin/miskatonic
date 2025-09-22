from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from models.question import QuestionModel, QuestionGetter
from models.quiz import QuizGenerator
from prometheus_fastapi_instrumentator import Instrumentator
from services.mongo import ServiceMongo
from services.question import ServiceQuestion
from services.quiz import ServiceQuiz


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201, ARG001
    """Handle MongoDB connection along app's lifespan."""
    ServiceMongo.connect()
    yield
    ServiceMongo.disconnect()


app = FastAPI(lifespan=lifespan)

Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/quiz/generate")
async def generate_quiz(params: QuizGenerator) -> None:
    """Generate a quiz."""
    ServiceQuiz.generate(
        total_questions=params.total_questions,
        subjects=params.subjects,
        use=params.use,
    )


@app.post("/question/create")
async def create_question(question: QuestionModel) -> ORJSONResponse:
    """Create question in MongoDB based on POST body."""
    try:
        ServiceQuestion.create(question=question)
        return ORJSONResponse(
            content={"message": "Question created successfully"},
            status_code=201,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/question/create_bulk")
async def create_questions(questions: list[QuestionModel]) -> ORJSONResponse:
    """Create questions in MongoDB based on POST body."""
    try:
        ServiceQuestion.create_all(questions=questions)
        return ORJSONResponse(
            content={"message": "Questions created successfully"},
            status_code=201,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/question/get_all")
async def get_all_questions() -> ORJSONResponse:
    """Get all questions from MongoDB."""
    try:
        questions = ServiceQuestion.list_all()
        questions = [question.model_dump() for question in questions]
        return ORJSONResponse(
            content=questions,
            status_code=201,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/question/get_some")
async def get_some_questions(params: QuestionGetter) -> ORJSONResponse:
    """Get some questions from MongoDB."""
    try:
        questions = ServiceQuestion.list_some(subjects=params.subjects, use=params.use)
        questions = [question.model_dump() for question in questions]
        return ORJSONResponse(
            content=questions,
            status_code=201,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
