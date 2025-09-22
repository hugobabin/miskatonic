"""Service for handling quiz generation."""

import random
from datetime import datetime, timezone
from typing import TypedDict

from models.question import QuestionModel
from models.quiz import Quiz
from services.mongo import ServiceMongo
from services.question import ServiceQuestion


class ServiceQuiz:
    """Static class for handling quiz generation."""

    @staticmethod
    def create(quiz: Quiz) -> None:
        """Insert a new quiz into MongoDB."""
        collection = ServiceMongo.get_collection("quiz")
        collection.insert_one(quiz)

    @staticmethod
    def generate(
        total_questions: int,
        subjects: list[str],
        use: str,
    ) -> list[QuestionModel]:
        """Generate a quiz with {total_questions} for said {subjects} and said {use}."""
        questions = ServiceQuestion.list_some(subjects=subjects, use=use)
        questions_sample = random.sample(questions, total_questions)
        quiz = Quiz(
            questions=questions_sample,
            subjects=subjects,
            use=use,
            metadata={"test": "toast"},
            date_creation={"$date": datetime.now(tz=timezone.utc).date},
            date_modification=None,
        )
        ServiceQuiz.create(quiz=quiz)
