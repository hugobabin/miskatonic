# ...existing code...
from fastapi import APIRouter, Request
from fastapi.responses import ORJSONResponse

from models.quiz import QuizGenerator
from services.quiz import ServiceQuiz
from services.util import handle_request_success

router = APIRouter(
    prefix="/quizs",
)


@router.get("/", tags=["quizs"], name="quizs")
async def get_quizs(request: Request) -> ORJSONResponse:
    # REFACTORING MVT // Retourne les quizs en JSONue
    quizs = ServiceQuiz.list_all()
    quizs = [quiz.model_dump() for quiz in quizs]
    return handle_request_success(request=request, data={"quizs": quizs})


@router.post("/generate", tags=["quizs"])
async def generate_quiz(params: QuizGenerator, request: Request) -> ORJSONResponse:
    # REFACTORING MVT // Génération via JSON, renvoie JSON
    ServiceQuiz.generate(
        total_questions=params.total_questions,
        subjects=params.subjects,
        use=params.use,
    )
    return handle_request_success(
        request=request,
        data={"success": True, "message": "Successfully generated a quiz."},
    )


@router.post("/{quiz}/archive", tags=["quizs"])
async def archive_quiz(quiz: str, request: Request) -> ORJSONResponse:
    # REFACTORING MVT // Archive et renvoie JSON
    ServiceQuiz.archive(quiz_id=quiz)
    return handle_request_success(
        request=request,
        data={"success": True, "message": f"Successfully archived quiz with id {quiz}"},
    )


# ...existing code...
