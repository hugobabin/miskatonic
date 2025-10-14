"""Service for handling persistency of questions in MongoDB."""

from datetime import datetime
from typing import TYPE_CHECKING

from bson import ObjectId

from models.question import QuestionCreator, QuestionDict, QuestionEditor, QuestionModel
from services.mongo import ServiceMongo
from services.util import ServiceUtil

if TYPE_CHECKING:
    from pymongo.collection import Collection


class ServiceQuestion:
    """Static class for handling questions."""

    @staticmethod
    def create(question: QuestionCreator) -> None:
        """Insert a new question into MongoDB."""
        new_question = QuestionModel(
            question=question.question,
            subject=question.subject,
            use=question.use,
            responses=question.responses,
            remark=question.remark,
            metadata={},
            date_creation=datetime.now(),
            date_modification=None,
        )

        collection: Collection[QuestionDict] = ServiceMongo.get_collection("questions")
        collection.insert_one(new_question.model_dump())

    @staticmethod
    def create_all(questions: list[QuestionModel]) -> None:
        """Insert new questions into MongoDB."""
        collection: Collection[QuestionDict] = ServiceMongo.get_collection("questions")
        to_insert = [question.model_dump() for question in questions]
        collection.insert_many(to_insert)

    @staticmethod
    def list_all() -> list[QuestionModel]:
        """Get all questions from MongoDB."""
        collection: Collection[QuestionDict] = ServiceMongo.get_collection("questions")
        found = collection.find()
        return [QuestionModel.model_validate(question) for question in found]

    @staticmethod
    def list_some(subjects: list[str], use: str) -> list[QuestionModel]:
        """Get some questions from MongoDB."""
        collection: Collection[QuestionDict] = ServiceMongo.get_collection("questions")
        found = collection.find({"use": use, "subject": {"$in": subjects}})
        return [QuestionModel.model_validate(question) for question in found]

    @staticmethod
    def edit(question_id: str, question: QuestionEditor) -> None:
        """Edit an existing question in MongoDB."""
        collection: Collection[QuestionDict] = ServiceMongo.get_collection("questions")
        question_id = ObjectId(question_id)
        query_filter = {"_id": question_id}
        dump = question.model_dump()
        dump["date_modification"] = datetime.now()  # noqa: DTZ005
        update_operation = {"$set": dump}
        collection.update_one(query_filter, update_operation, upsert=True)

    @staticmethod
    def archive(question_id: str) -> None:
        """Archive a question in MongoDB."""
        collection: Collection[QuestionDict] = ServiceMongo.get_collection("questions")
        question_id = ObjectId(question_id)
        query_filter = {"_id": question_id}
        update_operation = {"$set": {"active": False}}
        collection.update_one(query_filter, update_operation)

    @staticmethod
    def get_all_subjects() -> list[str]:
        """Get all existing quiz subjects from MongoDB."""
        questions = ServiceQuestion.list_all()
        return [question.subject for question in questions]

    @staticmethod
    def exists(question: str, subject: str, use: str) -> bool:
        """Cherche un doc avec même (subject, use) dont la question normalisée
        == question normalisée passée en entrée.
        """
        q_norm = ServiceUtil.normalize_question(question)
        col = ServiceMongo.get_collection("questions")

        cursor = col.find(
            {"subject": subject, "use": use},
            {"_id": 1, "question": 1},
        )

        for doc in cursor:
            if ServiceUtil.normalize_question(doc.get("question", "")) == q_norm:
                return True
        return False
