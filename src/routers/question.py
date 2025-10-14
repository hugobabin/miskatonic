# ...existing code...
from fastapi import APIRouter, Request, Body
from fastapi.responses import ORJSONResponse

from models.question import QuestionModel, QuestionEditor, QuestionCreator
from services.question import ServiceQuestion
from services.util import handle_request_success

router = APIRouter(
    prefix="/questions",
)


@router.get("/", tags=["questions"], name="questions")
async def get_questions(request: Request) -> ORJSONResponse:
    # REFACTORING MVT // Retourne la liste des questions au format JSON (API REST)
    questions = ServiceQuestion.list_all()
    questions = [question.model_dump() for question in questions]
    return handle_request_success(request=request, data={"questions": questions})


@router.post("/create", tags=["questions"], name="create_question")
async def create_question(
    request: Request,
    question: QuestionCreator = Body(...),
) -> ORJSONResponse:
    # REFACTORING MVT // Création via JSON body, renvoie JSON de succès
    ServiceQuestion.create(question=question)
    return handle_request_success(
        request=request,
        data={"success": True, "message": "Question créée avec succès!"},
    )


@router.post("/{question}/archive", tags=["questions"], name="archive_question")
async def archive_question(question: str, request: Request) -> ORJSONResponse:
    # REFACTORING MVT // Archive et renvoie JSON au lieu de RedirectResponse
    ServiceQuestion.archive(question_id=question)
    return handle_request_success(
        request=request, data={"success": True, "message": f"Archived {question}"}
    )


@router.post("/{question}/edit", tags=["questions"], name="edit_question")
async def edit_question(
    question: str,
    request: Request,
    data: QuestionEditor = Body(...),
) -> ORJSONResponse:
    # REFACTORING MVT // Edition via JSON body, renvoie JSON de succès
    ServiceQuestion.edit(question_id=question, question=data)
    return handle_request_success(
        request=request,
        data={"success": True, "message": "Question modifiée avec succès!"},
    )


# ...existing code...
