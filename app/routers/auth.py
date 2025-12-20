from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, auth_utils

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # چک کردن تکراری نبودن یوزرنیم
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="این نام کاربری قبلاً رزرو شده")

    new_user = models.User(
        username=user.username,
        hashed_password=auth_utils.hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth_utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="اطلاعات ورود غلط است")

    return {
        "access_token": auth_utils.create_access_token({"sub": str(user.id)}),
        "refresh_token": auth_utils.create_refresh_token({"sub": str(user.id)}),
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, auth_utils.SECRET_KEY, algorithms=[auth_utils.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="توکن اشتباه است")

        user_id = payload.get("sub")
        return {
            "access_token": auth_utils.create_access_token({"sub": user_id}),
            "refresh_token": refresh_token,  # معمولاً همان قبلی را برمی‌گردانیم یا یکی جدید می‌سازیم
            "token_type": "bearer"
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh Token منقضی شده، دوباره وارد شوید")