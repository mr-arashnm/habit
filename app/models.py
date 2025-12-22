import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, Text
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Enum, func, Text
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


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    reputation = Column(Integer, default=10)
    coins = Column(Integer, default=100)
    total_completed = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)

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

    owner = relationship("User", back_populates="promises")
    validations = relationship("Validation", back_populates="promise", cascade="all, delete-orphan")


class Validation(Base):
    __tablename__ = "validations"
    id = Column(Integer, primary_key=True, index=True)
    promise_id = Column(Integer, ForeignKey("promises.id"))
    validator_id = Column(Integer, ForeignKey("users.id"))
    weight = Column(Integer, default=1)

    promise = relationship("Promise", back_populates="validations")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
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


class StoreItem(Base):
    __tablename__ = "store_items"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    price = Column(Integer)
    effect_type = Column(String) # مثلا "reputation_boost" یا "remove_failure"
