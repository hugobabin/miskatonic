"""Quiz model based on BaseModel."""

from datetime import datetime
from typing import TypedDict

from backend.models.question import QuestionModel
from pydantic import BaseModel, ConfigDict, Field
from backend.services.util import ObjectIdValidator


class QuizModel(BaseModel):
    """Quiz."""

    id: ObjectIdValidator | None = Field(alias="_id")  # noqa: FA102
    questions: list[QuestionModel]
    subjects: list[str]
    use: str
    metadata: dict[str, str]
    date_creation: datetime
    date_modification: datetime | None  # noqa: FA102
    active: bool = Field(default=True)

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)


class QuizDict(TypedDict):
    """QuizDict."""

    id: str | None  # noqa: FA102
    questions: list[QuestionModel]
    subjects: list[str]
    use: str
    metadata: dict[str, str]
    date_creation: datetime
    date_modification: datetime | None  # noqa: FA102
    active: bool

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)


class QuizGenerator(BaseModel):
    """QuizGenerator."""

    total_questions: int
    subjects: list[str]
    use: str
