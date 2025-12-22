from sqlalchemy.orm import Session

from app import models


def create_notification(db: Session, user_id: int, content: str, promise_id: int = None):
    new_notif = models.Notification(
        user_id=user_id,
        content=content,
        promise_id=promise_id
    )
    db.add(new_notif)
    db.commit()