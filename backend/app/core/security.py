"""鉴权工具：JWT + bcrypt"""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import Users

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login", auto_error=False)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_token(user_id: int, role: str = "user") -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: Optional[str]) -> dict:
    if not token:
        raise ValueError("empty token")
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db),
) -> Users:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录凭证无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
        role = payload.get("role", "user")
    except (JWTError, ValueError, TypeError):
        raise credentials_error
    user = db.get(Users, user_id)
    if user is None or user.role != role:
        raise credentials_error
    return user


def require_admin(user: Users = Depends(get_current_user)) -> Users:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


def get_optional_user(
    credentials: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db),
) -> Optional[Users]:
    """可选鉴权：无 token 或 token 无效时返回 None（供公开演示接口使用）。"""
    if not credentials:
        return None
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None
