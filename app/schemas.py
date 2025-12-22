from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from .models import PromiseStatus  # وارد کردن Enum از مدل

# --- User Schemas ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(BaseModel):
    id: int
    username: Optional[str]
    phone_number: Optional[str]
    email: Optional[str]
    display_name: Optional[str]
    reputation: int
    coins: int
    is_onboarded: bool

    class Config:
        from_attributes = True

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None

# --- Promise Schemas ---
class PromiseBase(BaseModel):
    title: str
    description: Optional[str] = None
    reward: Optional[str] = None
    penalty: Optional[str] = None
    deadline: datetime
    visibility: str = "PUBLIC"

    @field_validator("visibility")
    @classmethod
    def uppercase_visibility(cls, v: str) -> str:
        return v.upper()

class PromiseCreate(PromiseBase):
    pass

class PromiseResponse(PromiseBase):
    id: int
    user_id: int
    status: PromiseStatus # استفاده از Enum واقعی
    evidence_text: Optional[str] = None
    created_at: datetime
    vouch_count: int = 0

    class Config:
        from_attributes = True

# --- Validation & Notification ---
class ValidationResponse(BaseModel):
    id: int
    validator_id: int
    weight: int

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

# --- Leaderboard & Store ---
class UserLeaderboard(BaseModel):
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

class ProfileComplete(BaseModel):
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('نام کاربری باید حداقل ۳ کاراکتر باشد')
        return v

class OnboardingData(BaseModel):
    username: str
    display_name: str
    password: str # ست کردن رمز عبور برای اولین بار
    bio: Optional[str] = None