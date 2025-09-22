"""Quiz model based on BaseModel."""

from models.question import QuestionModel
from pydantic import BaseModel, ConfigDict, Field
from services.util import ObjectIdValidator


class Quiz(BaseModel):
    """Quiz."""

    id: ObjectIdValidator = Field(alias="_id")
    questions: list[QuestionModel]
    subjects: list[str]
    use: str
    metadata: dict[str, str]
    date_creation: dict[str, str]
    date_modification: dict[str, str]

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)


class QuizGenerator(BaseModel):
    """Quiz generator."""

    total_questions: int
    subjects: list[str]
    use: str
