from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import schemas, crud, models
from ..dependencies import get_current_user

router = APIRouter(prefix="/promises", tags=["promises"])

@router.post("/", response_model=schemas.PromiseResponse)
def create_promise(promise: schemas.PromiseCreate, db: Session = Depends(get_db)):
    # در این مرحله فرض می‌کنیم کاربر با ID شماره 1 لاگین کرده است
    current_user_id = 1
    return crud.create_user_promise(db=db, promise=promise, user_id=current_user_id)

@router.get("/", response_model=List[schemas.PromiseResponse])
def get_all_promises(db: Session = Depends(get_db)):
    # گرفتن تمام قول‌ها و مرتب‌سازی بر اساس جدیدترین‌ها
    promises = db.query(models.Promise).order_by(models.Promise.id.desc()).all()
    return promises


@router.post("/{promise_id}/vouch")
def vouch_promise(promise_id: int, current_user_id: int = 999, db: Session = Depends(get_db)):
    # ۱. چک کردن اینکه آیا این کاربر قبلاً این قول را تایید کرده یا نه
    existing_vouch = db.query(models.Validation).filter(
        models.Validation.promise_id == promise_id,
        models.Validation.validator_id == current_user_id
    ).first()

    if existing_vouch:
        raise HTTPException(status_code=400, detail="شما قبلاً این قول را تایید کرده‌اید!")

    # ۲. پیدا کردن اعتبار کاربر تاییدکننده (فعلاً فرض می‌کنیم کاربر ۹۹۹ اعتبار ۲۰ دارد)
    validator_reputation = 20

    # ۳. ثبت تایید با وزنِ معادل اعتبار کاربر
    new_vouch = models.Validation(
        promise_id=promise_id,
        validator_id=current_user_id,
        weight=validator_reputation
    )
    db.add(new_vouch)

    # ۴. به‌روزرسانی وضعیت قول (مثلاً اگر مجموع وزن‌ها به ۱۰۰ رسید -> موفق)
    promise = db.query(models.Promise).filter(models.Promise.id == promise_id).first()
    total_weight = db.query(func.sum(models.Validation.weight)).filter(
        models.Validation.promise_id == promise_id
    ).scalar() or 0

    if total_weight >= 100:
        promise.status = "completed"

    db.commit()

    if promise.status == "completed":
        user = db.query(models.User).filter(models.User.id == promise.user_id).first()
        user.reputation += 5  # پاداش خوش‌قولی
        user.coins += 10  # پاداش سکه‌ای (اگر فیلدش را داشته باشی)
    return {"message": "تایید با موفقیت ثبت شد", "current_total": total_weight}


@router.post("/{promise_id}/complete")
def complete_promise_text(
        promise_id: int,
        report: str,  # دریافت گزارش به صورت متن
        current_user_id: int = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    promise = db.query(models.Promise).filter(
        models.Promise.id == promise_id,
        models.Promise.user_id == current_user_id
    ).first()

    if not promise:
        raise HTTPException(status_code=404, detail="قول پیدا نشد")

    if len(report) < 10:
        raise HTTPException(status_code=400, detail="گزارش خیلی کوتاهه، کمی بیشتر توضیح بده!")

    promise.evidence_text = report
    promise.status = "pending_approval"

    db.commit()
    return {"message": "گزارش ثبت شد. منتظر تایید دوستان باش!"}