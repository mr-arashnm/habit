from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from . import models
from .routers import auth, promises, users, notifications, websocket, messages, store

# ۱. ایجاد جداول دیتابیس (اگر از Alembic استفاده نمی‌کنی)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VaqtGhol API",
    description="Backend for the social habit-tracking app",
    version="1.0.0"
)

# ۲. تنظیمات CORS
# این بخش بسیار حیاتی است تا فرانت‌ا‌ند (React/Vue/HTML) بتواند به بک‌ا‌ند متصل شود
origins = [
    "http://localhost",
    "http://localhost:3000", # اگر فرانت روی این پورت بود
    "http://127.0.0.1:5500", # برای Live Server در VS Code
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ۳. اتصال روترها
# حتماً دقت کن که فایل‌های روتر در پوشه routers باشند و __init__.py داشته باشند
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(promises.router, prefix="/promises", tags=["Promises"])
app.include_router(users.router, prefix="/users", tags=["Users/Leaderboard"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSockets"])
app.include_router(messages.router, prefix="/messages", tags=["Direct Messages"])
app.include_router(store.router, prefix="/store", tags=["Store"])


# ۴. روت اصلی (Health Check)
@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Welcome to VaqtGhol API",
        "status": "Running",
        "docs": "/docs"
    }

# ۵. مدیریت فایل‌های استاتیک (در صورت نیاز به آپلود یا عکس پروفایل در آینده)
# app.mount("/static", StaticFiles(directory="static"), name="static")