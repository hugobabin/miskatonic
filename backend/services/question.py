"""Service for handling persistency of questions in MongoDB."""

from models.question import Question
from services.mongo import ServiceMongo


class ServiceQuestion:
    """Static class for handling questions."""

    @staticmethod
    def create(question: Question) -> None:
        """Insert a new question into MongoDB."""
        collection = ServiceMongo.get_collection("questions")
        collection.insert_one(question)

    @staticmethod
    def create_all(questions: list[Question]) -> None:
        """Insert new questions into MongoDB."""
        collection = ServiceMongo.get_collection("question")
        collection.insert_many(questions)

    @staticmethod
    def list_all() -> list[Question]:
        """Get all questions from MongoDB."""
        collection = ServiceMongo.get_collection("question")
        return collection.find()

    @staticmethod
    def list_some(subjects: list[str], use: str) -> list[Question]:
        """Get some questions from MongoDB."""
        collection = ServiceMongo.get_collection("question")
        return collection.find({"use": use, "subject": {"$in": subjects}})

    @staticmethod
    def edit(question: Question) -> None:
        """Edit an existing question in MongoDB."""
        collection = ServiceMongo.get_collection("question")
        # complete here

    @staticmethod
    def archive(id: int) -> None:
        """Archive a question in MongoDB."""
        collection = ServiceMongo.get_collection("question")
        # complete here
