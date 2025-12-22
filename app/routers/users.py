from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas
from ..dependencies import get_current_user

router = APIRouter()


# --- ۱. دریافت اطلاعات پروفایل من ---
@router.get("/me", response_model=schemas.UserFullProfile)
def get_my_full_profile(current_user: models.User = Depends(get_current_user)):
    """مشاهده پروفایل کامل توسط خود کاربر (شامل اطلاعات حساس)"""
    return current_user


@router.patch("/me")
def update_my_profile(
        obj_in: schemas.UserUpdate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    """ویرایش اطلاعات توسط کاربر"""
    # بررسی تکراری نبودن یوزرنیم جدید (اگر کاربر بخواهد یوزرنیم را عوض کند)
    if obj_in.username:
        existing_user = db.query(models.User).filter(models.User.username == obj_in.username).first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="این نام کاربری قبلاً رزرو شده است")

    # آپدیت فیلدها
    for field, value in obj_in.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    return {"message": "پروفایل با موفقیت به‌روزرسانی شد"}


# --- ۲. دریافت لیست برترین‌ها ---
@router.get("/leaderboard", response_model=List[schemas.UserLeaderboard])
def get_leaderboard(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.reputation.desc()).limit(10).all()


@router.get("/profile/{username}", response_model=schemas.UserProfilePublic)
def get_user_public_profile(username: str, db: Session = Depends(get_db)):
    # ۱. پیدا کردن کاربر بر اساس یوزرنیم
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر مورد نظر پیدا نشد")

    # ۲. واکشی قول‌های عمومی این کاربر (مثلاً فقط قول‌هایی که حذف نشده‌اند)
    user_promises = db.query(models.Promise).filter(
        models.Promise.user_id == user.id
    ).order_by(models.Promise.created_at.desc()).all()

    # ۳. آماده‌سازی خروجی
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "bio": user.bio, # اگر در مدل یوزر فیلد بیو داری
        "coins": user.coins,
        "reputation": user.reputation,
        "promises": user_promises,
        "stats": {
            "total_promises": len(user_promises),
            "completed": len([p for p in user_promises if p.status == "completed"]),
            "failed": len([p for p in user_promises if p.status == "failed"])
        }
    }