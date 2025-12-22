from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas
from ..dependencies import get_current_user
from ..models import User

router = APIRouter()


# ۱. دریافت لیست گفتگوها (اینباکس)
@router.get("/inbox", response_model=List[schemas.ConversationResponse])
def get_inbox(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    conversations = db.query(models.Conversation).filter(
        (models.Conversation.user1_id == current_user.id) |
        (models.Conversation.user2_id == current_user.id)
    ).order_by(models.Conversation.updated_at.desc()).all()
    return conversations


# ۲. دریافت تاریخچه پیام‌های یک گفتگوی خاص
@router.get("/history/{conversation_id}", response_model=List[schemas.MessageResponse])
def get_chat_history(
        conversation_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    # اول چک می‌کنیم که این گفتگو متعلق به این کاربر هست یا نه (امنیت)
    conv = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if not conv or (conv.user1_id != current_user.id and conv.user2_id != current_user.id):
        raise HTTPException(status_code=403, detail="عدم دسترسی به این گفتگو")

    messages = db.query(models.DirectMessage).filter(
        models.DirectMessage.conversation_id == conversation_id
    ).order_by(models.DirectMessage.created_at.asc()).all()

    # علامت‌گذاری پیام‌ها به عنوان خوانده شده
    db.query(models.DirectMessage).filter(
        models.DirectMessage.conversation_id == conversation_id,
        models.DirectMessage.sender_id != current_user.id
    ).update({"is_read": True})
    db.commit()

    return messages


# ویرایش پیام
@router.patch("/edit/{message_id}")
def edit_message(message_id: int, new_content: str, current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    msg = db.query(models.DirectMessage).filter(models.DirectMessage.id == message_id).first()
    if not msg or msg.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="اجازه ویرایش ندارید")

    msg.content = new_content
    msg.is_edited = True
    db.commit()
    return {"status": "edited"}


# حذف پیام (Soft Delete)
@router.delete("/delete/{message_id}")
def delete_message(message_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msg = db.query(models.DirectMessage).filter(models.DirectMessage.id == message_id).first()
    if not msg or msg.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="اجازه حذف ندارید")

    msg.is_deleted = True  # متن پیام را نگه می‌داریم ولی نمایش نمی‌دهیم
    db.commit()
    return {"status": "deleted"}


# جستجو در پیام‌های یک گفتگو
@router.get("/search/{conversation_id}")
def search_messages(conversation_id: int, query: str, db: Session = Depends(get_db)):
    results = db.query(models.DirectMessage).filter(
        models.DirectMessage.conversation_id == conversation_id,
        models.DirectMessage.content.contains(query),
        models.DirectMessage.is_deleted == False
    ).all()
    return results