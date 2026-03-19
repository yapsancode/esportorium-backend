import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.services import auth as auth_service

bearer_scheme = HTTPBearer()

# Maps each role to its ordinal level in the hierarchy.
ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.player: 0,
    UserRole.team_captain: 1,
    UserRole.organizer: 2,
    UserRole.moderator: 3,
    UserRole.admin: 4,
    UserRole.super_admin: 5,
}


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise credentials_exc

    if payload.get("type") != "access":
        raise credentials_exc

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise credentials_exc

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exc

    user = auth_service.get_user_by_id(session, user_id)
    if not user:
        raise credentials_exc
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    return user


def require_role(*roles: UserRole):
    """Exact role match. Usage: Depends(require_role(UserRole.admin, UserRole.super_admin))"""

    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency


def require_min_role(min_role: UserRole):
    """Minimum role in hierarchy. Usage: Depends(require_min_role(UserRole.organizer))"""
    min_level = ROLE_HIERARCHY[min_role]

    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if ROLE_HIERARCHY[current_user.role] < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires at least '{min_role.value}' role",
            )
        return current_user

    return dependency
