from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int
    full_name: str
    email: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# User Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "admin"

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

# Department Schemas
class DepartmentCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class DepartmentOut(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

# ClassRoom Schemas
class ClassRoomCreate(BaseModel):
    name: str
    subject_code: str
    faculty_name: str
    schedule_time: str
    department_id: int

class ClassRoomOut(BaseModel):
    id: int
    name: str
    subject_code: str
    faculty_name: str
    schedule_time: str
    department_id: int

    class Config:
        from_attributes = True

# Student Schemas
class StudentCreate(BaseModel):
    roll_number: str
    full_name: str
    email: EmailStr
    year: str
    department_id: int

class StudentOut(BaseModel):
    id: int
    roll_number: str
    full_name: str
    email: str
    year: str
    department_id: int
    photo_url: Optional[str] = None
    is_enrolled: bool
    created_at: datetime
    department_name: Optional[str] = None

    class Config:
        from_attributes = True

# Attendance Schemas
class AttendanceLogRequest(BaseModel):
    student_id: int
    class_id: Optional[int] = None
    date: str
    time: str
    status: str
    confidence: float

class AttendanceOut(BaseModel):
    id: int
    student_id: int
    student_name: str
    roll_number: str
    department_name: str
    class_id: Optional[int] = None
    subject_name: Optional[str] = "General Subject"
    subject_code: Optional[str] = "GEN"
    date: str
    time: str
    status: str
    confidence: float
    verified_by: str

    class Config:
        from_attributes = True

# AI Recognition Request & Response
class FaceRecognizeRequest(BaseModel):
    image_base64: str
    class_id: Optional[int] = None

class FaceRecognizeResult(BaseModel):
    matched: bool
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    roll_number: Optional[str] = None
    confidence: float
    status: str # Present, Late, Unknown
    message: str
    bounding_box: Optional[dict] = None

# Analytics & AI Summary
class AnalyticsSummary(BaseModel):
    total_students: int
    present_today: int
    absent_today: int
    late_today: int
    unknown_faces_count: int
    overall_attendance_pct: float
    recent_activity: List[dict]
    department_breakdown: List[dict]
    ai_insights: List[str]

class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class SettingUpdate(BaseModel):
    key: str
    value: str
