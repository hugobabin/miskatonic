"""Service for handling security operations."""

from typing import Any, Iterable, Set

from fastapi import Depends, HTTPException, Request, status

from services.authentification import get_roles_for_user


def require_session_user(request: Request) -> dict[str, Any]:
    """Require session user."""
    user = None
    try:
        user = request.session.get("user") if hasattr(request, "session") else None
    except Exception:
        user = None

    if not user:
        uid = request.headers.get("x-user-id")
        uname = request.headers.get("x-username")
        if uid and uname:
            user = {"id": int(uid), "username": uname}

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


def require_roles(roles: Iterable[str]) -> Any:  # noqa: ANN401
    """Require roles."""
    required: Set[str] = set(roles)

    def _dep(user=Depends(require_session_user)) -> Any:  # noqa: ANN001, ANN401, B008
        """Depend."""
        uid = int(user["id"])
        roles_for_user = get_roles_for_user(uid)
        if not roles_for_user.intersection(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        return user

    return _dep
