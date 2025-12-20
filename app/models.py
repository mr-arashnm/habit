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

class PromiseStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)  # ذخیره پسورد هش شده
    reputation = Column(Integer, default=10)  # همه با اعتبار ۱۰ شروع می‌کنند
    coins = Column(Integer, default=0)
    total_completed = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    
    # سیستم امتیاز و وزن اعتبار
    coins = Column(Integer, default=0)
    reputation_score = Column(Float, default=1.0) # همان وزن تایید که گفتی
    
    promises = relationship("Promise", back_populates="owner")

class Promise(Base):
    __tablename__ = "promises"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    
    # هسته اصلی قول
    reward = Column(String)    # پاداش (هویج)
    penalty = Column(String)   # مجازات (چماق)
    
    deadline = Column(DateTime)
    status = Column(Enum(PromiseStatus), default=PromiseStatus.PENDING)
    visibility = Column(Enum(VisibilityEnum), default=VisibilityEnum.PUBLIC)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # این مهمه

    evidence_text = Column(Text, nullable=True)  # گزارش متنی انجام قول

    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="promises")
    
    # تعاملات
    validations = relationship("Validation", back_populates="promise")
    comments = relationship("Comment", back_populates="promise")

class Validation(Base):
    __tablename__ = "validations"

    id = Column(Integer, primary_key=True)
    promise_id = Column(Integer, ForeignKey("promises.id"))
    validator_id = Column(Integer, ForeignKey("users.id"))
    weight = Column(Float) # وزنی که تاییدکننده در آن لحظه داشته

    promise = relationship("Promise", back_populates="validations")



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


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # گیرنده اعلان
    content = Column(String)  # متن اعلان
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # اختیاری: لینک دادن به یک قول خاص
    promise_id = Column(Integer, nullable=True)