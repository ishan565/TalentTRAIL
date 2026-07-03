"""FastAPI dependencies: DB session + current authenticated user."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ACCESS_TOKEN, decode_token
from app.db import models
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token, expected_type=ACCESS_TOKEN)
    if not payload:
        raise credentials_exc
    user_id = payload.get("sub")
    user = db.get(models.User, int(user_id)) if user_id else None
    if not user or not user.is_active:
        raise credentials_exc
    return user
