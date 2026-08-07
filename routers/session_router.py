from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/sessions", tags=["Attendance Sessions"])

def parse_time_str(t_str: str) -> Optional[datetime]:
    if not t_str:
        return None
    t_str = t_str.strip()
    formats = ["%I:%M %p", "%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M%p"]
    for fmt in formats:
        try:
            dt = datetime.strptime(t_str, fmt)
            now = datetime.now()
            return now.replace(hour=dt.hour, minute=dt.minute, second=0, microsecond=0)
        except ValueError:
            pass
    return None

def is_within_session_time_window(start_time_raw: str, end_time_raw: str) -> tuple[bool, str]:
    now = datetime.now()
    
    start_dt = None
    end_dt = None

    if start_time_raw and "to" in start_time_raw.lower():
        parts = start_time_raw.lower().split("to")
        start_dt = parse_time_str(parts[0])
        end_dt = parse_time_str(parts[1])
    else:
        start_dt = parse_time_str(start_time_raw)
        end_dt = parse_time_str(end_time_raw)

    if start_dt and now < start_dt:
        return False, f"Attendance session has not started yet (Scheduled Start: {start_time_raw})"

    if end_dt and now > end_dt:
        return False, f"Attendance session has ended for today (Session closed at {end_time_raw or start_time_raw})"

    return True, "Session time window valid"

@router.get("")
def get_sessions(db: Session = Depends(get_db)):
    return db.query(models.AttendanceSession).order_by(models.AttendanceSession.id.desc()).all()

@router.post("")
def create_attendance_session(
    title: str,
    subject_code: str,
    faculty_name: str,
    date: str,
    start_time: str,
    end_time: str,
    department_id: Optional[int] = None,
    year: Optional[str] = None,
    section: Optional[str] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_admin_or_faculty)
):
    session = models.AttendanceSession(
        title=title,
        subject_code=subject_code,
        faculty_name=faculty_name,
        department_id=department_id,
        year=year,
        section=section,
        date=date,
        start_time=start_time,
        end_time=end_time,
        status="Active"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/validate-student")
def validate_student_active_session(
    class_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user)
):
    """Executes 7-step pre-flight validation for the specific selected class before opening camera."""
    # 1. Is student logged in?
    if user.role == "student":
        student = db.query(models.Student).filter(models.Student.user_id == user.id).first()
    else:
        student = db.query(models.Student).first()

    if not student:
        return {
            "allowed": False,
            "reason": "Student profile not found",
            "step": 1
        }

    # 2. Is there an active attendance session for this specific class?
    query = db.query(models.AttendanceSession).filter(models.AttendanceSession.status == "Active")
    
    if class_id:
        cls = db.query(models.ClassRoom).filter(models.ClassRoom.id == class_id).first()
        if cls:
            query = query.filter(models.AttendanceSession.subject_code == cls.subject_code)

    active_session = query.order_by(models.AttendanceSession.id.desc()).first()

    if not active_session:
        return {
            "allowed": False,
            "reason": "No Active Attendance Session found for this class",
            "step": 2
        }

    # 3. Department match check
    if active_session.department_id and student.department_id and active_session.department_id != student.department_id:
        return {
            "allowed": False,
            "reason": f"Department mismatch: Session is for {active_session.department_id}, you belong to {student.department_id}",
            "step": 3
        }

    # 4. Academic Year match check
    if active_session.year and student.year and active_session.year != student.year:
        return {
            "allowed": False,
            "reason": f"Academic Year mismatch: Session is for {active_session.year}, you are in {student.year}",
            "step": 4
        }

    # 5. Section match check
    if active_session.section and hasattr(student, "section") and student.section and active_session.section != student.section:
        return {
            "allowed": False,
            "reason": f"Section mismatch: Session is for {active_session.section}, you belong to {student.section}",
            "step": 5
        }

    # 6. Enrollment check
    if not student.is_enrolled:
        return {
            "allowed": False,
            "reason": "You are not enrolled in face dataset engine for this course",
            "step": 6
        }

    # 7. Time Window Validation Check (Specific to this class session schedule)
    time_valid, time_msg = is_within_session_time_window(active_session.start_time, active_session.end_time)
    if not time_valid:
        return {
            "allowed": False,
            "reason": f"[{active_session.subject_code}] {time_msg}",
            "step": 7
        }

    # All 7 validations passed
    return {
        "allowed": True,
        "session_id": active_session.id,
        "subject_code": active_session.subject_code,
        "faculty_name": active_session.faculty_name,
        "student_name": student.full_name,
        "roll_number": student.roll_number,
        "department_name": student.department.name if student.department else "General",
        "year": student.year,
        "section": getattr(student, "section", "Section A"),
        "reason": "All 7 Pre-Flight Validations Passed! Camera authorization granted."
    }

@router.post("/{session_id}/complete")
def complete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.AttendanceSession).filter(models.AttendanceSession.id == session_id).first()
    if session:
        session.status = "Completed"
        db.commit()
    return {"message": "Session completed"}
