import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, auth_utils
from ..dependencies import get_current_user
from ..models import OTPType, OTPCode, User
from ..services.notifier import Notifier
from ..services.sms_service import SMSService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/check-user")
def check_user(identifier: str, db: Session = Depends(get_db)):
    """
    مرحله اول: کاربر ایمیل یا موبایل را وارد می‌کند.
    اگر اکانت داشت: می‌گوییم پسورد بزن.
    اگر نداشت: کد تایید می‌فرستیم.
    """
    user = db.query(User).filter((User.email == identifier) | (User.phone_number == identifier)).first()

    if user:
        return {"status": "existing_user", "message": "لطفاً رمز عبور خود را وارد کنید یا درخواست کد بدهید."}

    # کاربر جدید است -> ارسال کد تایید
    return send_otp_request(identifier, db)


@router.post("/send-otp")
def send_otp_request(identifier: str, db: Session = Depends(get_db)):
    # چک کردن فاصله زمانی (مثلاً حداقل ۲ دقیقه بین هر درخواست)
    last_otp = db.query(OTPCode).filter(OTPCode.identifier == identifier).first()
    if last_otp:
        elapsed_time = datetime.utcnow() - last_otp.last_request_at
        if elapsed_time.total_seconds() < 120:  # ۱۲۰ ثانیه
            raise HTTPException(
                status_code=429,
                detail=f"لطفاً {int(120 - elapsed_time.total_seconds())} ثانیه دیگر صبر کنید."
            )
    #    """ارسال مجدد کد یا ارسال برای کاربر جدید/فراموشی رمز"""
    otp_type = OTPType.EMAIL if "@" in identifier else OTPType.PHONE
    code = Notifier.generate_code()

    # حذف کدهای قبلی این کاربر
    db.query(OTPCode).filter(OTPCode.identifier == identifier).delete()

    new_otp = OTPCode(identifier=identifier, code=code, otp_type=otp_type)
    db.add(new_otp)
    db.commit()

    if otp_type == OTPType.PHONE:
        Notifier.send_sms(identifier, code)
    else:
        Notifier.send_email(identifier, code)

    return {"status": "otp_sent", "message": "کد تایید ۲ دقیقه‌ای ارسال شد."}


@router.post("/verify-and-login")
def verify_and_login(identifier: str, code: str, db: Session = Depends(get_db)):
    """تایید کد و ورود مستقیم (برای کاربر جدید یا فراموشی رمز)"""
    db_otp = db.query(OTPCode).filter(
        OTPCode.identifier == identifier,
        OTPCode.code == code
    ).first()

    if not db_otp or db_otp.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="کد منقضی شده یا اشتباه است")

    user = db.query(User).filter((User.email == identifier) | (User.phone_number == identifier)).first()

    if not user:
        # ساخت کاربر جدید (موقت)
        # در اینجا در فرانت‌ا‌ند باید بعدا از او بخواهید نام کاربری و پسورد انتخاب کند
        user = User(
            username=f"user_{identifier.split('@')[0] if '@' in identifier else identifier[-4:]}",
            email=identifier if "@" in identifier else None,
            phone_number=identifier if "@" not in identifier else None,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # پاک کردن کد استفاده شده
    db.delete(db_otp)
    db.commit()

    # تولید توکن JWT
    token = auth_utils.create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "is_new_user": not user.hashed_password}


@router.post("/register")
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # ۱. بررسی تکراری نبودن شماره موبایل
    existing_user = db.query(models.User).filter(models.User.phone_number == user_data.phone_number).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="این شماره قبلاً ثبت شده است")

    # ۲. ایجاد کاربر غیرفعال
    new_user = models.User(
        username=user_data.username,
        phone_number=user_data.phone_number,
        hashed_password=auth_utils.get_password_hash(user_data.password),
        is_active=False,
        is_phone_verified=False
    )
    db.add(new_user)
    db.flush()  # آیدی کاربر را می‌گیریم بدون اینکه تراکنش نهایی شود

    # ۳. تولید کد OTP و ارسال واقعی
    otp_code = SMSService.generate_code()

    # ارسال پیامک
    sms_sent = SMSService.send_otp(user_data.phone_number, otp_code)

    if not sms_sent:
        db.rollback()
        raise HTTPException(status_code=500, detail="خطا در ارسال پیامک. لطفاً دوباره تلاش کنید.")

    # ۴. ذخیره کد در دیتابیس برای تایید (با زمان انقضا)
    new_otp = models.OTPCode(
        phone_number=user_data.phone_number,
        code=otp_code,
        expires_at=datetime.utcnow() + datetime.timedelta(minutes=2)
    )
    db.add(new_otp)
    db.commit()

    return {"message": "کد تایید با موفقیت ارسال شد"}


@router.post("/onboard")
def complete_onboarding(
        data: schemas.OnboardingData,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if current_user.is_onboarded:
        raise HTTPException(status_code=400, detail="شما قبلاً این مراحل را انجام داده‌اید")

    # ۱. چک کردن یوزرنیم
    existing = db.query(models.User).filter(models.User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="این نام کاربری قبلاً انتخاب شده است")

    # ۲. ثبت اطلاعات و اهدای جایزه
    current_user.username = data.username
    current_user.display_name = data.display_name
    current_user.hashed_password = auth_utils.get_password_hash(data.password)
    current_user.bio = data.bio
    current_user.is_onboarded = True

    # جایزه برای تکمیل پروفایل
    current_user.coins += 50

    db.commit()
    return {"message": "تبریک! پروفایل تکمیل شد و ۵۰ سکه هدیه گرفتی."}


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth_utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="اطلاعات ورود غلط است")

    return {
        "access_token": auth_utils.create_access_token({"sub": str(user.id)}),
        "refresh_token": auth_utils.create_refresh_token({"sub": str(user.id)}),
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, auth_utils.SECRET_KEY, algorithms=[auth_utils.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="توکن اشتباه است")

        user_id = payload.get("sub")
        return {
            "access_token": auth_utils.create_access_token({"sub": user_id}),
            "refresh_token": refresh_token,  # معمولاً همان قبلی را برمی‌گردانیم یا یکی جدید می‌سازیم
            "token_type": "bearer"
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh Token منقضی شده، دوباره وارد شوید")