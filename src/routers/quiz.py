from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, ORJSONResponse

from models.quiz import QuizGenerator
from services.quiz import ServiceQuiz
from services.util import get_templates, handle_request_success

router = APIRouter(
    prefix="/quizs",
)


@router.get("/", response_class=HTMLResponse, tags=["quizs"])
async def get_quizs(request: Request) -> HTMLResponse:
    """Get all quizs from MongoDB."""
    quizs = ServiceQuiz.list_all()
    quizs = [quiz.model_dump() for quiz in quizs]
    return get_templates().TemplateResponse(
        request=request,
        name="quizs.html",
        context={"quizs": quizs},
    )


@router.post("/generate", tags=["quizs"])
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


@router.post("/{quiz}/archive", tags=["quizs"])
async def archive_quiz(quiz: str, request: Request) -> ORJSONResponse:
    """Archive a quiz in MongoDB."""
    ServiceQuiz.archive(quiz_id=quiz)
    return handle_request_success(
        request=request,
        message=f"Successfully archived quiz with id {quiz}",
    )
