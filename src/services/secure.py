from typing import Iterable, Set
from fastapi import Depends, HTTPException, status
from src.services.authentification import get_current_user, get_roles_for_user

def require_roles(roles: Iterable[str]):
    required: Set[str] = set(roles)
    def _dep(user = Depends(get_current_user)):  # verify JWT + is_active
        uid = int(user[0])                        # (id, username, ...)
        if not (get_roles_for_user(uid) & required):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return user                               # Reuse username in route
    return _dep
