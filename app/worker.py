from celery import Celery
from celery.schedules import crontab
from database import SessionLocal
import tasks # فایلی که الان می‌سازیم

# تنظیم آدرس Redis (اگر روی سیستم خودت است همین آدرس پیش‌فرض است)
celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# تعریف زمان‌بندی: هر ۱ دقیقه یک‌بار چک کند
celery_app.conf.beat_schedule = {
    "check-expired-promises-every-minute": {
        "task": "app.worker.monitor_promises",
        "schedule": 60.0,
    },
}

@celery_app.task
def monitor_promises():
    db = SessionLocal()
    try:
        tasks.check_expired_promises(db)
    finally:
        db.close()