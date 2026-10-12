from functools import wraps
from typing import Callable, TypeVar
from sqlalchemy.exc import SQLAlchemyError
from app.core.exceptions import RepositoryError

T = TypeVar("T")

def repository_class(cls: type[T]) -> type[T]:
    """Wrap persistence failures, rollback the session, and preserve root cause."""
    for name in ("create", "get_by_id", "list", "update", "delete"):
        method = getattr(cls, name, None)
        if method is None:
            continue
        setattr(cls, name, _wrap(method))
    return cls

def _wrap(method: Callable):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except SQLAlchemyError as error:
            self._session.rollback()
            raise RepositoryError(
                "Database operation failed",
                details={"repository": type(self).__name__, "operation": method.__name__},
            ) from error
    return wrapped

