"""Question model based on BaseModel."""

from datetime import datetime
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field

from services.util import ObjectIdValidator


class ResponseModel(BaseModel):
    """ResponseModel."""

    answer: str
    isCorrect: bool = False  # noqa: N815


class QuestionModel(BaseModel):
    """Question."""

    id: ObjectIdValidator = Field(default=None, alias="_id")  # ← défaut None
    question: str
    subject: str
    use: str
    responses: list[ResponseModel]
    remark: str | None  # noqa: FA102
    metadata: dict[str, str]
    date_creation: datetime
    date_modification: datetime | None  # noqa: FA102
    active: bool = Field(default=True)

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)


class QuestionDict(TypedDict):
    """QuestionDict."""

    id: str | None  # noqa: FA102
    question: str
    subject: str
    use: str
    responses: list[dict[str, str | bool]]  # noqa: FA102
    remark: str
    metadata: list[dict[str, str]]
    date_creation: datetime
    date_modification: datetime | None  # noqa: FA102
    active: bool


class QuestionGetter(BaseModel):
    """QuestionGetter."""

    subjects: list[str]
    use: str
