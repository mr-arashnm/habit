from pydantic import BaseModel, field_validator # در نسخه‌های جدید Pydantic از field_validator استفاده می‌شود
from datetime import datetime
from typing import Optional, List

class Token(BaseModel):
    access_token: str
    refresh_token: str # اضافه شد
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None

# --- اسکیمای کاربر ---
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    reputation: int
    coins: int  # اضافه شد برای نمایش در پروفایل
    total_completed: int # اضافه شد برای آمار داشبورد
    total_failed: int    # اضافه شد برای آمار داشبورد

    class Config:
        from_attributes = True

# --- اسکیمای قول (Promise) ---
class PromiseBase(BaseModel):
    title: str
    reward: Optional[str] = None
    penalty: Optional[str] = None
    deadline: datetime
    visibility: str = "PUBLIC"

    @field_validator("visibility") # جایگزین validator قدیمی
    @classmethod
    def uppercase_visibility(cls, v: str) -> str:
        return v.upper()

class PromiseCreate(PromiseBase):
    pass

class PromiseResponse(PromiseBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    vouch_count: int = 0

    class Config:
        from_attributes = True

# --- اسکیمای احراز هویت (Token) ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

# --- بقیه اسکیماها (بدون تغییر) ---
class UserLeaderboard(BaseModel):
    id: int
    username: str
    reputation: int
    class Config:
        from_attributes = True

class StoreItemResponse(BaseModel):
    id: int
    name: str
    description: str
    price: int
    effect_type: str
    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: int
    content: str
    is_read: bool
    created_at: datetime
    promise_id: Optional[int] = None

    class Config:
        from_attributes = True