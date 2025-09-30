from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, ORJSONResponse

from models.question import QuestionModel
from services.question import ServiceQuestion
from services.util import get_templates, handle_request_success

router = APIRouter(
    prefix="/questions",
)


@router.get("/", response_class=HTMLResponse, tags=["questions"])
async def get_questions(request: Request) -> HTMLResponse:
    """Get all questions from MongoDB."""
    questions = ServiceQuestion.list_all()
    questions = [question.model_dump() for question in questions]
    return get_templates().TemplateResponse(
        request=request,
        name="questions.html",
        context={"questions": questions},
    )


@router.post("/create", tags=["questions"])
async def create_question(question: QuestionModel, request: Request) -> ORJSONResponse:
    """Create question in MongoDB based on POST body."""
    ServiceQuestion.create(question=question)
    return handle_request_success(
        request=request,
        message="Succesfully created question.",
    )


@router.post("/create_bulk", tags=["questions"])
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


@router.post("/{question}/archive", tags=["questions"])
async def archive_question(question: str, request: Request) -> ORJSONResponse:
    """Archive a question in MongoDB."""
    ServiceQuestion.archive(question_id=question)
    return handle_request_success(
        request=request,
        message=f"Successfully archived question with id {question}",
    )


@router.post("/{question}/edit", tags=["questions"])
async def edit_question(
    question: str,
    data: QuestionModel,
    request: Request,
) -> ORJSONResponse:
    """Edit a question in MongoDB."""
    ServiceQuestion.edit(question_id=question, question=data)
    return handle_request_success(
        request=request,
        message=f"Successfully edited question with id {question}",
    )
