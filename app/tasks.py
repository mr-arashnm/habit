from datetime import datetime
from . import models


def check_expired_promises(db):
    now = datetime.utcnow()
    # قول‌هایی که وقتشان تمام شده و هنوز وضعیتشان "pending" است
    expired = db.query(models.Promise).filter(
        models.Promise.deadline < now,
        models.Promise.status == "pending"
    ).all()

    for p in expired:
        p.status = "failed"
        # کسر اعتبار از کاربر به دلیل شکست در قول
        user = db.query(models.User).filter(models.User.id == p.user_id).first()
        if user:
            user.reputation -= 10

    db.commit()