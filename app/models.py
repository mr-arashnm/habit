from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
import datetime


Base = declarative_base()

class VisibilityEnum(enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    FRIENDS_ONLY = "friends_only"


class PromiseStatus(str, enum.Enum):
    PENDING = "pending"
    PENDING_APPROVAL = "pending_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class OTPType(str, enum.Enum):
    PHONE = "phone"
    EMAIL = "email"


class OTPCode(Base):
    __tablename__ = "otp_codes"
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, index=True) # می‌تواند ایمیل یا شماره موبایل باشد
    code = Column(String)
    otp_type = Column(Enum(OTPType))
    last_request_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + datetime.timedelta(minutes=2))


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)

    phone_number = Column(String, unique=True, index=True, nullable=True)
    is_phone_verified = Column(Boolean, default=False)  # تایید اختصاصی موبایل

    email = Column(String, unique=True, index=True, nullable=True)
    is_email_verified = Column(Boolean, default=False)  # تایید اختصاصی ایمیل

    hashed_password = Column(String)
    is_active = Column(Boolean, default=False)

    display_name = Column(String, nullable=True)  # نام نمایشی (مثلاً: آرش ناصری)
    bio = Column(String, nullable=True)
    is_onboarded = Column(Boolean, default=False)  # آیا مراحل اولیه را تکمیل کرده؟

    reputation = Column(Integer, default=10)
    coins = Column(Integer, default=100)
    total_completed = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)

    reputation_multiplier = Column(Float, default=1.0)
    multiplier_expiry = Column(DateTime, nullable=True)

    # روابط: حذف کاربر باعث حذف قول‌ها و نوتیفیکیشن‌های او می‌شود
    promises = relationship("Promise", back_populates="owner", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Promise(Base):
    __tablename__ = "promises"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    reward = Column(String, nullable=True)
    penalty = Column(String, nullable=True)
    deadline = Column(DateTime)
    status = Column(Enum(PromiseStatus), default=PromiseStatus.PENDING)
    evidence_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    parent_id = Column(Integer, ForeignKey("promises.id"), nullable=True)

    owner = relationship("User", back_populates="promises")
    validations = relationship("Validation", back_populates="promise", cascade="all, delete-orphan")


class Validation(Base):
    __tablename__ = "validations"
    id = Column(Integer, primary_key=True, index=True)
    promise_id = Column(Integer, ForeignKey("promises.id"))
    validator_id = Column(Integer, ForeignKey("users.id"))
    weight = Column(Integer, default=1)

    promise = relationship("Promise", back_populates="validations")


class NotificationType(str, enum.Enum):
    VOUCH_RECEIVED = "vouch_received"  # وقتی کسی قولت رو تایید می‌کنه
    PROMISE_COMPLETED = "promise_completed"  # وقتی قول تایید نهایی می‌شه
    PROMISE_FAILED = "promise_failed"  # وقتی زمان قول تموم می‌شه و شکست می‌خوری
    SYSTEM_MESSAGE = "system_message"  # پیام‌های مدیر یا جوایز خاص
    REMINDER = "reminder"  # یادآوری برای ارسال گزارش


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    type = Column(Enum(NotificationType), default=NotificationType.SYSTEM_MESSAGE)
    title = Column(String)  # عنوان کوتاه (مثلاً: تایید جدید!)
    content = Column(String)  # متن کامل

    # لینک دادن به یک آبجکت خاص (مثلاً آیدی قولی که براش نوتیف اومده)
    link_id = Column(Integer, nullable=True)

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notifications")



class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    promise_id = Column(Integer, ForeignKey("promises.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # روابط
    promise = relationship("Promise", back_populates="comments")
    author = relationship("User")


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    blacklisted_at = Column(DateTime, default=datetime.datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"))
    user2_id = Column(Integer, ForeignKey("users.id"))
    last_message = Column(String)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow) # برای مرتب‌سازی لیست چت‌ها


class DirectMessage(Base):
    __tablename__ = "direct_messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    is_read = Column(Boolean, default=False)

    # فیلدهای جدید برای حرفه‌ای شدن
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)  # حذف منطقی (Soft Delete)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)


class StoreItem(Base):
    __tablename__ = "store_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Integer)
    category = Column(String, index=True) # avatar, powerup, discount
    stock = Column(Integer, default=0)
    discount_code = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("store_items.id"))
    purchased_at = Column(DateTime, default=datetime.datetime.utcnow)
    revealed_code = Column(String, nullable=True)