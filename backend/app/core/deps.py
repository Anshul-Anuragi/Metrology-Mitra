import uuid
from typing import Callable, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
        if not token_data.sub:
            raise credentials_exception
    except (jwt.PyJWTError, ValidationError):
        raise credentials_exception

    try:
        user_id = uuid.UUID(token_data.sub)
    except ValueError:
        raise credentials_exception

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated",
        )
    return user


def require_role(allowed_roles: List[UserRole]) -> Callable:
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted: requires one of {[r.value for r in allowed_roles]} roles",
            )
        return current_user

    return role_checker


# Role-specific dependency shortcuts
require_inspector = require_role([UserRole.INSPECTOR, UserRole.SUPERVISOR, UserRole.ADMIN])
require_supervisor = require_role([UserRole.SUPERVISOR, UserRole.ADMIN])
require_admin = require_role([UserRole.ADMIN])

