from typing import Iterable, Set
from fastapi import Depends, HTTPException, status, Request

from src.services.authentification import get_roles_for_user

# Services to secure routes
def require_session_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user  # dict: {"id": ..., "username": ...}

# Check that the authenticated user has at least one of the required roles
def require_roles(roles: Iterable[str]):
    required: Set[str] = set(roles)
    def _dep(user = Depends(require_session_user)):
        uid = int(user["id"])
        roles_for_user = get_roles_for_user(uid)
        if not roles_for_user.intersection(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden"
            )
        return user 
    return _dep
