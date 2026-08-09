import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine, Base
from config import settings

# Import routers
from routers import (
    auth_router,
    student_router,
    department_router,
    class_router,
    faculty_router,
    session_router,
    attendance_router,
    analytics_router,
    reports_router,
    notifications_router,
    settings_router
)

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full Stack AI Face-Based Attendance System API Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)}
    )

# Configure CORS safely for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "https://facedetectionfront.vercel.app"],
    allow_origin_regex=r"https://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded static files (face images, unknown captures)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Routers under API v1 prefix
api_v1 = settings.API_V1_STR
app.include_router(auth_router.router, prefix=api_v1)
app.include_router(student_router.router, prefix=api_v1)
app.include_router(department_router.router, prefix=api_v1)
app.include_router(class_router.router, prefix=api_v1)
app.include_router(faculty_router.router, prefix=api_v1)
app.include_router(session_router.router, prefix=api_v1)
app.include_router(attendance_router.router, prefix=api_v1)
app.include_router(analytics_router.router, prefix=api_v1)
app.include_router(reports_router.router, prefix=api_v1)
app.include_router(notifications_router.router, prefix=api_v1)
app.include_router(settings_router.router, prefix=api_v1)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "docs": "/docs",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
