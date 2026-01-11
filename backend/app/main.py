from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .database import Base, engine
from .routers import invoice
from .config import UPLOAD_DIR

# Create database tables
Base.metadata.create_all(bind=engine)

# Create upload directory
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="出纳发票识别系统",
    description="发票识别 → 分类汇总 → 记账分录",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for serving images
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(invoice.router)


@app.get("/")
def root():
    return {"message": "出纳发票识别系统 API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
