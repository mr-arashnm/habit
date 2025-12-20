from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# اگر از PostgreSQL استفاده می‌کنی، آدرس را اینجا بگذار
# فعلاً برای شروع سریع و تست، از SQLite استفاده می‌کنیم که فایلش کنار پروژه ساخته شود
SQLALCHEMY_DATABASE_URL = "sqlite:///./vaqtghol.db"
# برای PostgreSQL: "postgresql://user:password@localhost/dbname"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} # این مورد فقط برای SQLite لازم است
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# این تابع کلیدی است که در Routerها به عنوان Dependency تزریق می‌کنیم
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()