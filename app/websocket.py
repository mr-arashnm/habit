# بخشی از روت وب‌سوکت در websocket.py
import datetime
from sqlalchemy.orm import Session
from . import models


async def handle_direct_message(db: Session, sender_id: int, receiver_id: int, text: str):
    # ۱. پیدا کردن یا ساختن کانورزیشن (یکتا بین دو نفر)
    conv = db.query(models.Conversation).filter(
        ((models.Conversation.user1_id == sender_id) & (models.Conversation.user2_id == receiver_id)) |
        ((models.Conversation.user1_id == receiver_id) & (models.Conversation.user2_id == sender_id))
    ).first()

    if not conv:
        conv = models.Conversation(user1_id=sender_id, user2_id=receiver_id)
        db.add(conv)
        db.flush()

    # ۲. ذخیره پیام
    new_msg = models.DirectMessage(conversation_id=conv.id, sender_id=sender_id, content=text)
    conv.last_message = text  # به‌روزرسانی برای لیست اینباکس
    conv.updated_at = datetime.datetime.utcnow()

    db.add(new_msg)
    db.commit()
    return new_msg