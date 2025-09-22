"""Service for handling useful functions and decorators."""

import os

from dotenv import load_dotenv


class ServiceUtil:
    """Static class for handling useful functions."""

    @staticmethod
    def load_env() -> None:
        """Load environment file."""
        load_dotenv(".env")

    @staticmethod
    def get_env(var: str, default: str = "") -> str:
        """Get environment {var} or {default} value."""
        return os.getenv(var, default)


# class DefineCollection:
#     """Decorator for handling MongoDB collections easier."""

#     def __init__(self, collection_name: str, model_type: type[T]) -> None:
#         """Define {collection_name}."""
#         self.collection_name = collection_name
#         self.model_type = model_type

#     def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
#         """Define wrapper."""

#         @wraps(func)
#         def wrapper(*args: tuple, **kwargs: dict) -> Callable[..., Any]:
#             collection: Collection[T] = ServiceMongo.get_collection(
#                 self.collection_name,
#             )
#             return func(*args, collection=collection, **kwargs)

#         return wrapper
