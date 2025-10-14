"""Service for handling quiz generation."""

import random
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from models.quiz import QuizDict, QuizModel
from services.mongo import ServiceMongo
from services.question import ServiceQuestion

if TYPE_CHECKING:
    from pymongo.collection import Collection


class ServiceQuiz:
    """Static class for handling quiz generation."""

    @staticmethod
    def create(quiz: QuizModel) -> None:
        """Insert a new quiz into MongoDB."""
        collection: Collection[QuizDict] = ServiceMongo.get_collection("quizs")
        collection.insert_one(quiz.model_dump())

    @staticmethod
    def list_all() -> list[QuizModel]:
        """Get all quizs from MongoDB."""
        collection: Collection[QuizDict] = ServiceMongo.get_collection("quizs")
        found = collection.find()
        return [QuizModel.model_validate(quiz) for quiz in found]

    @staticmethod
    def archive(quiz_id: int) -> None:
        """Archive a quiz in MongoDB."""
        collection: Collection[QuizDict] = ServiceMongo.get_collection("quizs")
        query_filter = {"_id": quiz_id}
        update_operation = {"$set": {"active": False}}
        collection.update_one(query_filter, update_operation)

    @staticmethod
    def generate(
        total_questions: int,
        subjects: list[str],
        use: str,
    ) -> None:
        """Generate a quiz with {total_questions} for said {subjects} and said {use}."""
        questions = ServiceQuestion.list_some(subjects=subjects, use=use)
        questions_sample = random.sample(
            questions,
            min(total_questions, len(questions)),
        )
        quiz = QuizModel(
            id=None,
            questions=questions_sample,
            subjects=subjects,
            use=use,
            metadata={"test": "toast"},
            date_creation=datetime.now(tz=timezone.utc),
            date_modification=None,
            active=True,
        )
        ServiceQuiz.create(quiz=quiz)
