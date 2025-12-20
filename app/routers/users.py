from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas

router = APIRouter()


# --- ۱. دریافت اطلاعات پروفایل من ---
@router.get("/me", response_model=schemas.UserLeaderboard)
def get_my_profile(current_user_id: int = 999, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == current_user_id).first()
    if not user:
        # اگر کاربر تستی وجود نداشت، اینجا یکی می‌سازیم (فقط برای مرحله توسعه)
        user = models.User(id=999, username="User_Test", coins=500, reputation=20)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# --- ۲. دریافت لیست برترین‌ها ---
@router.get("/leaderboard", response_model=List[schemas.UserLeaderboard])
def get_leaderboard(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.reputation.desc()).limit(10).all()


# --- ۳. لیست آیتم‌های فروشگاه ---
@router.get("/store", response_model=List[schemas.StoreItemResponse])
def get_store_items(db: Session = Depends(get_db)):
    items = db.query(models.StoreItem).all()
    # اگر فروشگاه خالی بود، به صورت خودکار چند آیتم اضافه کن
    if not items:
        seed_items = [
            models.StoreItem(name="بمب اعتبار", description="+5 اعتبار اضافه", price=100, effect_type="rep_boost"),
            models.StoreItem(name="پاک‌کن شکست", description="حذف یک رکورد منفی", price=300, effect_type="fail_remove")
        ]
        db.add_all(seed_items)
        db.commit()
        return seed_items
    return items


# --- ۴. عملیات خرید ---
@router.post("/buy/{item_id}")
def buy_item(item_id: int, current_user_id: int = 999, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == current_user_id).first()
    item = db.query(models.StoreItem).filter(models.StoreItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="آیتم پیدا نشد")

    if user.coins < item.price:
        raise HTTPException(status_code=400, detail="سکه کافی نداری!")

    # کسر سکه و اعمال تغییرات
    user.coins -= item.price
    if item.effect_type == "rep_boost":
        user.reputation += 5
    elif item.effect_type == "fail_remove" and user.total_failed > 0:
        user.total_failed -= 1

    db.commit()
    db.refresh(user)
    return {"status": "success", "new_balance": user.coins, "message": f"آیتم {item.name} خریداری شد"}