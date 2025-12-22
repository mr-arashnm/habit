from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..dependencies import get_current_user
from .. import models, schemas

# این خط دقیقاً همان چیزی است که Uvicorn دنبالش می‌گردد:
router = APIRouter()


@router.get("/", response_model=List[schemas.NotificationResponse])
def get_notifications(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db),
        unread_only: bool = False
):
    query = db.query(models.Notification).filter(models.Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(models.Notification.is_read == False)

    return query.order_by(models.Notification.created_at.desc()).limit(50).all()


@router.post("/mark-all-read")
def mark_all_as_read(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "تمام اعلان‌ها خوانده شد"}