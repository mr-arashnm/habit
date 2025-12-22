from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, auth_utils, schemas
from ..dependencies import get_current_user
from ..models import OTPCode, User, OTPType
from ..services.notifier import Notifier

router = APIRouter()


@router.post("/check-user")
def check_user(identifier: str, type: str, db: Session = Depends(get_db)):
    """
    مرحله ۱: تشخیص نوع ورود (پسورد یا کد تایید)
    """
    if type == "email":
        user = db.query(User).filter( (User.email == identifier) | (User.username == identifier)).first()
    elif type == "phone":
        user = (User.phone_number == identifier).first()

    # اگر کاربر وجود دارد و رمز عبور هم تعریف کرده است
    if user and user.hashed_password:
        return {
            "status": "needs_password",
            "message": "لطفاً رمز عبور خود را وارد کنید.",
            "method": "password"
        }

    # اگر کاربر وجود ندارد یا رمز ندارد -> ارسال کد تایید
    return send_otp_logic(identifier,type, db)


def send_otp_logic(identifier: str,type: str, db: Session = Depends(get_db)):
    """تابع کمکی برای ارسال کد تایید"""
    # جلوگیری از ارسال مکرر (Rate Limit)
    last_otp = db.query(OTPCode).filter(OTPCode.identifier == identifier).first()
    if last_otp:
        # استفاده از timezone.utc برای رفع باگ utcnow
        now = datetime.now(timezone.utc)
        last_req = last_otp.last_request_at.replace(tzinfo=timezone.utc)
        if now - last_req < timedelta(seconds=120):
            return {"status": "wait", "remaining": 120 - (now - last_req).seconds}

    code = Notifier.generate_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=2)

    # حذف کدهای قبلی و ذخیره جدید
    db.query(OTPCode).filter(OTPCode.identifier == identifier).delete()
    new_otp = OTPCode(identifier=identifier, code=code, expires_at=expires_at)
    db.add(new_otp)
    db.commit()

    # ارسال کد (پیامک یا ایمیل)
    if type == "email":
        Notifier.send_email(identifier, code)
    elif type == "phone":
        Notifier.send_sms(identifier, code)

    return {
        "status": "needs_otp",
        "message": "کد تایید برای شما ارسال شد.",
        "method": "otp"
    }


@router.post("/login-with-password")
def login_password(identifier: str, password: str, db: Session = Depends(get_db)):
    """ورود با رمز عبور"""
    user = db.query(User).filter(
        (User.email == identifier) | (User.phone_number == identifier) | (User.username == identifier)
    ).first()

    if not user or not auth_utils.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="رمز عبور اشتباه است.")

    token = auth_utils.create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/verify-otp")
def verify_otp(identifier: str, code: str, db: Session = Depends(get_db)):
    db_otp = db.query(OTPCode).filter(OTPCode.identifier == identifier, OTPCode.code == code).first()

    if not db_otp or db_otp.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="کد اشتباه یا منقضی شده است.")

    user = db.query(User).filter((User.email == identifier) | (User.phone_number == identifier)).first()

    is_new_user = False
    if not user:
        is_new_user = True
        # ساخت یک کاربر خام (بدون نام کاربری و مشخصات)
        user = User(
            username=f"temp_{int(datetime.now().timestamp())}",  # یوزرنیم موقت عددی
            phone_number=identifier if "@" not in identifier else None,
            email=identifier if "@" in identifier else None,
            is_active=True,
            is_onboarded=False  # این فیلد خیلی مهم است
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    db.delete(db_otp)
    db.commit()

    token = auth_utils.create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
        "needs_onboarding": not user.is_onboarded  # اگر بار اول باشد، True برمی‌گردد
    }


@router.post("/complete-onboarding")
def complete_onboarding(
        data: schemas.UserOnboarding,  # شامل نام، یوزرنیم انتخابی و پسورد
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # ۱. چک کردن اینکه یوزرنیم تکراری نباشد
    existing = db.query(User).filter(User.username == data.username).first()
    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=400, detail="این نام کاربری قبلاً انتخاب شده است.")

    # ۲. ذخیره اطلاعات نهایی
    current_user.full_name = data.full_name
    current_user.username = data.username
    current_user.hashed_password = auth_utils.get_password_hash(data.password)
    current_user.is_onboarded = True  # حالا دیگر کاربر قدیمی محسوب می‌شود

    # ۳. اهدای جایزه کلون (اگر از طریق لینک کسی آمده بود)
    # در اینجا می‌توانید منطق سکه را هم اضافه کنید
    current_user.coins += 50

    db.commit()
    return {"status": "success", "message": "ثبت‌نام شما با موفقیت تکمیل شد."}