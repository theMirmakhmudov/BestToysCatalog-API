from fastapi import Depends
from app.db.models.user import User, RoleEnum
from app.core.response import BaseHTTPException, ErrorCodes
from app.core.deps import get_current_user

def IsAuthenticated(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise BaseHTTPException(401, ErrorCodes.AUTH_FAILED, "Authentication required.")
    return current_user

def IsAdmin(current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.admin:
        raise BaseHTTPException(403, ErrorCodes.FORBIDDEN, "Admin privileges required.")
    return current_user