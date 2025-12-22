# app/services/notification_service.py
from ..models import Notification, NotificationType
from app.managers.notifications_manager import manager
from sqlalchemy.orm import Session

async def create_notification(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    notif_type: NotificationType,
    link_id: int = None
):
    # ۱. ذخیره در دیتابیس (برای وقتی که کاربر آفلاین است)
    new_notif = Notification(
        user_id=user_id,
        title=title,
        content=content,
        type=notif_type,
        link_id=link_id
    )
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)

    # ۲. ارسال آنی در صورت آنلاین بودن کاربر
    await manager.send_personal_message({
        "id": new_notif.id,
        "title": title,
        "content": content,
        "type": notif_type.value,
        "link_id": link_id,
        "created_at": str(new_notif.created_at)
    }, user_id)