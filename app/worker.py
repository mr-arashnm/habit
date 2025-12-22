from celery import Celery
from celery.schedules import crontab
from database import SessionLocal
import models
from datetime import datetime

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)


@celery_app.task
def monitor_promises():
    # ایجاد یک Session تازه برای این تسک
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        # پیدا کردن قول‌های منقضی شده
        expired_promises = db.query(models.Promise).filter(
            models.Promise.deadline < now,
            models.Promise.status == models.PromiseStatus.PENDING
        ).all()

        for promise in expired_promises:
            promise.status = models.PromiseStatus.FAILED
            # جریمه کاربر
            if promise.owner:
                promise.owner.reputation -= 5
                promise.owner.total_failed += 1

        db.commit()
    except Exception as e:
        print(f"Error in Celery Task: {e}")
        db.rollback()
    finally:
        db.close()  # بسیار حیاتی برای جلوگیری از کراش دیتابیس


# تنظیم زمان‌بندی هر ۱ دقیقه
celery_app.conf.beat_schedule = {
    "check-deadlines-every-minute": {
        "task": "worker.monitor_promises",
        "schedule": 60.0,
    },
}