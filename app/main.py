from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import models
from app.database import engine
from app.routers import promises, users, auth

# ساخت جداول دیتابیس در هنگام بالا آمدن برنامه (اگر وجود نداشته باشند)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vaqtghol API", version="0.1.0")



# این را قبل از include_router اضافه کن
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# رجیستر کردن روترها
app.include_router(promises.router)
app.include_router(users.router)
app.include_router(auth.router)
@app.get("/")
def root():
    return {"message": "Welcome to Vaqtghol! The vibe is high. 🚀"}