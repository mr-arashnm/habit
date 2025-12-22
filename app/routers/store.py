from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..dependencies import get_current_user
from .. import models, schemas

router = APIRouter()


# ۱. لیست محصولات با قابلیت فیلتر بر اساس دسته و جستجوی متنی
@router.get("/items", response_model=List[schemas.StoreItemResponse])
def list_items(
        category: Optional[str] = None,
        search: Optional[str] = Query(None, min_length=2),
        db: Session = Depends(get_db)
):
    query = db.query(models.StoreItem).filter(models.StoreItem.stock > 0)

    if category:
        query = query.filter(models.StoreItem.category == category)

    if search:
        # جستجو در نام یا توضیحات
        query = query.filter(
            (models.StoreItem.name.contains(search)) |
            (models.StoreItem.description.contains(search))
        )

    return query.all()


# ۲. خرید محصول
@router.post("/buy/{item_id}", response_model=schemas.PurchaseResponse)
def buy_item(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.StoreItem).filter(models.StoreItem.id == item_id).first()

    if not item or item.stock <= 0:
        raise HTTPException(status_code=404, detail="محصول موجود نیست")

    if current_user.coins < item.price:
        raise HTTPException(status_code=400, detail="سکه کافی ندارید. بیشتر تلاش کن!")

    # کسر موجودی و سکه
    current_user.coins -= item.price
    item.stock -= 1

    # ثبت خرید
    new_purchase = models.Purchase(
        user_id=current_user.id,
        item_id=item.id,
        final_price=item.price,
        revealed_code=item.discount_code
    )

    db.add(new_purchase)
    db.commit()
    db.refresh(new_purchase)

    return new_purchase


# ۳. تاریخچه خریدهای من
@router.get("/my-purchases", response_model=List[schemas.PurchaseResponse])
def get_purchase_history(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Purchase).filter(models.Purchase.user_id == current_user.id).order_by(
        models.Purchase.purchased_at.desc()).all()