from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..database import get_db
from ..dependencies import get_current_user
from .. import models, schemas, config

router = APIRouter()


# ۱. دریافت لیست تمام قول‌ها (برای فید اصلی)
@router.get("/", response_model=List[schemas.PromiseResponse])
def get_promises(db: Session = Depends(get_db)):
    # محاسبه تعداد تاییدها برای هر قول به صورت داینامیک
    promises = db.query(models.Promise).all()
    for p in promises:
        p.vouch_count = db.query(models.Validation).filter(models.Validation.promise_id == p.id).count()
    return promises


# ۲. ثبت قول جدید
@router.post("/", response_model=schemas.PromiseResponse)
def create_promise(promise: schemas.PromiseCreate, current_user: models.User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    new_promise = models.Promise(
        **promise.model_dump(),
        user_id=current_user.id,
        status=models.PromiseStatus.PENDING
    )
    db.add(new_promise)
    db.commit()
    db.refresh(new_promise)
    return new_promise


# ۳. ارسال گزارش انجام قول (Text Evidence)
@router.post("/{promise_id}/complete")
def complete_promise(
        promise_id: int,
        report: str,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    promise = db.query(models.Promise).filter(
        models.Promise.id == promise_id,
        models.Promise.user_id == current_user.id
    ).first()

    if not promise:
        raise HTTPException(status_code=404, detail="قولی پیدا نشد")

    if promise.status != models.PromiseStatus.PENDING:
        raise HTTPException(status_code=400, detail="این قول قبلاً تعیین تکلیف شده")

    promise.evidence_text = report
    promise.status = models.PromiseStatus.PENDING_APPROVAL
    db.commit()
    return {"message": "گزارش ثبت شد. منتظر تایید دوستان باش!"}


# ۴. منطق تایید قول توسط دیگران (Vouch)
@router.post("/{promise_id}/vouch")
def vouch_promise(
        promise_id: int,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    promise = db.query(models.Promise).filter(models.Promise.id == promise_id).first()

    if not promise:
        raise HTTPException(status_code=404, detail="قول پیدا نشد")

    if promise.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="نمی‌تونی به قول خودت رای بدی!")

    # چک کردن رای تکراری
    existing_vouch = db.query(models.Validation).filter(
        models.Validation.promise_id == promise_id,
        models.Validation.validator_id == current_user.id
    ).first()

    if existing_vouch:
        raise HTTPException(status_code=400, detail="قبلاً به این قول رای دادی")

    # ثبت تایید جدید
    new_vouch = models.Validation(promise_id=promise_id, validator_id=current_user.id)
    db.add(new_vouch)

    # شمارش تاییدها
    total_vouches = db.query(models.Validation).filter(models.Validation.promise_id == promise_id).count()

    # اگر تاییدها به حد نصاب (مثلاً ۳ نفر) رسید:
    if total_vouches >= config.settings.VOUCH_THRESHOLD and promise.status == models.PromiseStatus.PENDING_APPROVAL:
        promise.status = models.PromiseStatus.COMPLETED
        # پاداش به صاحب قول
        promise.owner.reputation += 10
        promise.owner.coins += 50
        promise.owner.total_completed += 1

        # اطلاع‌رسانی به صاحب قول
        notification = models.Notification(
            user_id=promise.user_id,
            content=f"تبریک! قول '{promise.title}' تایید نهایی شد و جایزه گرفتی.",
            promise_id=promise.id
        )
        db.add(notification)

    db.commit()
    return {"message": "رای تایید شما ثبت شد", "current_vouches": total_vouches}