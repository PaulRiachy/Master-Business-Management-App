from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, verify_password
from app.db.session import get_db
from app.models import User
from app.schemas.schemas import LoginRequest, TokenOut, UserOut

router = APIRouter()


@router.post("/auth/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": create_access_token(user.id), "user": user}


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
