from sqlalchemy.orm import Session
from . import models, schemas

def create_user_promise(db: Session, promise: schemas.PromiseCreate, user_id: int):
    db_promise = models.Promise(**promise.model_dump(), user_id=user_id)
    db.add(db_promise)
    db.commit()
    db.refresh(db_promise)
    return db_promise