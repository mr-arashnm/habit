from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..dependencies import get_current_user
from .. import models, schemas

# این خط دقیقاً همان چیزی است که Uvicorn دنبالش می‌گردد:
router = APIRouter()


@router.get("/", response_model=List[schemas.NotificationResponse])
def get_my_notifications(
        current_user_id: int = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # توجه: اگر current_user_id در نسخه جدید مدل، کل آبجکت User را برمی‌گرداند،
    # از user.id استفاده کن.
    uid = current_user_id.id if hasattr(current_user_id, 'id') else current_user_id

    return db.query(models.Notification).filter(
        models.Notification.user_id == uid
    ).order_by(models.Notification.created_at.desc()).all()


@router.post("/{notif_id}/read")
def mark_as_read(
        notif_id: int,
        current_user_id: int = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    uid = current_user_id.id if hasattr(current_user_id, 'id') else current_user_id

    notif = db.query(models.Notification).filter(
        models.Notification.id == notif_id,
        models.Notification.user_id == uid
    ).first()

    if notif:
        notif.is_read = True
        db.commit()
    return {"status": "success"}