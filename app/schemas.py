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


class UserMinimalResponse(BaseModel):
    id: int
    username: str
    display_name: Optional[str] = None

    class Config:
        from_attributes = True

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


class PromiseDetailResponse(BaseModel):
    id: int
    title: str
    description: str
    target_date: datetime
    is_completed: bool
    status: str  # active, failed, completed
    created_at: datetime

    # اطلاعات سازنده قول برای نمایش در پروفایل کوچک بالای صفحه
    creator: UserMinimalResponse

    # آمار سریع
    vouch_count: int
    view_count: int = 0  # اگر خواستی سیستم بازدید اضافه کنی

    class Config:
        from_attributes = True

class PromiseCreate(PromiseBase):
    pass

class PromiseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None

class PromiseResponse(PromiseBase):
    id: int
    user_id: int
    status: PromiseStatus # استفاده از Enum واقعی
    evidence_text: Optional[str] = None
    created_at: datetime
    vouch_count: int = 0

    class Config:
        from_attributes = True

class UserProfilePublic(BaseModel):
    id: int
    username: str
    display_name: Optional[str]
    bio: Optional[str]
    coins: int
    reputation: int
    promises: List[PromiseResponse] # لیست قول‌های او
    stats: dict # آمار کلی (تعداد موفق/شکست)

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
    type: str
    title: str
    content: str
    link_id: Optional[int]
    is_read: bool
    created_at: datetime

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

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    content: str
    is_read: bool
    is_edited: bool
    is_deleted: bool  # اگر True بود، فرانت‌ا‌ند متن را نشان نمی‌دهد (مثلاً می‌نویسد: این پیام حذف شده است)
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    user1_id: int
    user2_id: int
    last_message: Optional[str]
    updated_at: datetime

    # اطلاعات اضافی که معمولاً با Join در بک‌ا‌ند پر می‌کنیم تا فرانت‌ا‌ند راحت باشد
    other_user_username: Optional[str] = None
    other_user_display_name: Optional[str] = None
    unread_count: int = 0  # تعداد پیام‌های خوانده نشده برای کاربر فعلی

    class Config:
        from_attributes = True

class MessageUpdate(BaseModel):
    content: str # متن جدید پیام

class MessageCreate(BaseModel):
    receiver_id: int
    content: str

class ChatSearchQuery(BaseModel):
    query: str
    limit: int = 20

class UserFullProfile(BaseModel):
    id: int
    username: str
    email: Optional[str]
    phone_number: Optional[str]
    display_name: Optional[str]
    bio: Optional[str]
    coins: int
    reputation: int
    is_onboarded: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    username: Optional[str] = None
    # اینجا کاربر می‌تواند ایمیلش را هم اضافه یا ویرایش کند
    email: Optional[str] = None

class StoreItemResponse(BaseModel):
    id: int
    name: str
    description: str
    price: int
    category: str
    stock: int
    image_url: Optional[str]

class PurchaseResponse(BaseModel):
    id: int
    item_name: str
    purchased_at: datetime
    revealed_code: Optional[str]

class TrendingPromiseResponse(PromiseResponse):
    adoptions_count: int # تعداد دفعاتی که این قول توسط دیگران Adopt شده
    creator: UserMinimalResponse

    class Config:
        from_attributes = True