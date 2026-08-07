import os
import uuid
import base64
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models, schemas, auth
from config import settings
from services.ai_client import ai_client
from services.email_service import notify_unknown_face_alert, notify_absentee

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.get("", response_model=List[schemas.AttendanceOut])
def get_attendance_logs(
    date: Optional[str] = None,
    department_id: Optional[int] = None,
    student_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(auth.get_current_user)
):
    query = db.query(models.Attendance).join(models.Student)

    # Student Isolation: If logged in as student, return ONLY their own attendance records
    if user and user.role == "student":
        student = db.query(models.Student).filter(models.Student.user_id == user.id).first()
        if student:
            query = query.filter(models.Attendance.student_id == student.id)
        else:
            return []
    elif student_id:
        query = query.filter(models.Attendance.student_id == student_id)

    if date:
        query = query.filter(models.Attendance.date == date)
    if department_id:
        query = query.filter(models.Student.department_id == department_id)

    logs = query.order_by(models.Attendance.id.desc()).all()
    res = []
    for l in logs:
        sub_name = "Course Lecture"
        sub_code = "CLASS"
        if l.session_id:
            sess = db.query(models.AttendanceSession).filter(models.AttendanceSession.id == l.session_id).first()
            if sess:
                sub_name = sess.title.replace(" Attendance Session", "").replace(" Session", "")
                sub_code = sess.subject_code
        elif l.classroom:
            sub_name = l.classroom.name
            sub_code = l.classroom.subject_code
        else:
            first_cls = db.query(models.ClassRoom).first()
            if first_cls:
                sub_name = first_cls.name
                sub_code = first_cls.subject_code

        res.append({
            "id": l.id,
            "student_id": l.student_id,
            "student_name": l.student.full_name if l.student else "Unknown",
            "roll_number": l.student.roll_number if l.student else "-",
            "department_name": l.student.department.name if l.student and l.student.department else "-",
            "class_id": l.class_id,
            "subject_name": sub_name,
            "subject_code": sub_code,
            "date": l.date,
            "time": l.time,
            "status": l.status,
            "confidence": l.confidence,
            "verified_by": l.verified_by
        })
    return res

@router.post("/recognize", response_model=schemas.FaceRecognizeResult)
def recognize_and_mark_attendance(
    req: schemas.FaceRecognizeRequest,
    db: Session = Depends(get_db)
):
    """Processes dynamic video stream frame from webcam via AI service."""
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    current_time_str = now.strftime("%I:%M:%S %p")

    # Fetch enrolled student embeddings
    embeddings = db.query(models.FaceEmbedding).all()
    emb_list = [
        {"student_id": e.student_id, "embedding": e.embedding_data} for e in embeddings
    ]

    # Invoke AI Recognition
    ai_res = ai_client.recognize_face(req.image_base64, emb_list)

    if not ai_res.get("matched"):
        # Handle Unknown Face Detection
        try:
            img_bytes = base64.b64decode(req.image_base64.split(",")[-1])
            filename = f"unknown_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(settings.UPLOAD_DIR, "unknown", filename)
            with open(filepath, "wb") as f:
                f.write(img_bytes)

            unknown_rec = models.UnknownFace(
                image_path=f"/uploads/unknown/{filename}",
                camera_location="Main Camera Feed"
            )
            db.add(unknown_rec)
            db.commit()

            # Trigger Admin Security Notification
            sec_notif = models.Notification(
                title="Unknown Face Alert",
                message=f"Unrecognized face captured at {current_time_str}",
                type="security"
            )
            db.add(sec_notif)
            db.commit()

            notify_unknown_face_alert("admin@attendance.ai", current_time_str, "Main Camera Feed")
        except Exception as e:
            pass

        return schemas.FaceRecognizeResult(
            matched=False,
            confidence=0.0,
            status="Unknown",
            message="Unrecognized face - Security Alert Created"
        )

    matched_student_id = ai_res["student_id"]
    student = db.query(models.Student).filter(models.Student.id == matched_student_id).first()
    if not student:
        return schemas.FaceRecognizeResult(
            matched=False,
            confidence=0.0,
            status="Unknown",
            message="Matched student profile missing"
        )

    # STRICT SESSION VALIDATION: Must have an Active attendance session running for the selected class!
    query = db.query(models.AttendanceSession).filter(models.AttendanceSession.status == "Active")
    if req.class_id:
        cls = db.query(models.ClassRoom).filter(models.ClassRoom.id == req.class_id).first()
        if cls:
            query = query.filter(models.AttendanceSession.subject_code == cls.subject_code)

    active_session = query.order_by(models.AttendanceSession.id.desc()).first()

    if not active_session:
        return schemas.FaceRecognizeResult(
            matched=False,
            student_id=student.id,
            student_name=student.full_name,
            roll_number=student.roll_number,
            confidence=0.0,
            status="Rejected",
            message="No Active Attendance Session found for selected class."
        )

    # Time Window Validation (reject if class time has passed, e.g. 09:00 AM to 10:00 AM)
    from routers.session_router import is_within_session_time_window
    time_valid, time_msg = is_within_session_time_window(active_session.start_time, active_session.end_time)
    if not time_valid:
        return schemas.FaceRecognizeResult(
            matched=False,
            student_id=student.id,
            student_name=student.full_name,
            roll_number=student.roll_number,
            confidence=0.0,
            status="Rejected",
            message=time_msg
        )

    # Duplicate Attendance Prevention: Per-Session check (student can attend multiple classes per day)
    existing_session_log = db.query(models.Attendance).filter(
        models.Attendance.student_id == student.id,
        models.Attendance.session_id == active_session.id
    ).first()

    if existing_session_log:
        return schemas.FaceRecognizeResult(
            matched=True,
            student_id=student.id,
            student_name=student.full_name,
            roll_number=student.roll_number,
            confidence=ai_res.get("confidence", 0.95),
            status=existing_session_log.status,
            message=f"Attendance already logged for {active_session.subject_code} session today ({existing_session_log.status})"
        )

    # Determine status: Present vs Late
    # Configured Late Threshold check (e.g. 09:15)
    late_setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == "late_threshold").first()
    late_cutoff = late_setting.value if late_setting else settings.DEFAULT_LATE_THRESHOLD
    
    current_time_short = now.strftime("%H:%M")
    status_flag = "Late" if current_time_short > late_cutoff else "Present"

    attendance_record = models.Attendance(
        student_id=student.id,
        session_id=active_session.id,
        class_id=req.class_id,
        date=today_str,
        time=current_time_str,
        status=status_flag,
        confidence=ai_res.get("confidence", 0.92),
        verified_by="AI Face Scanner"
    )
    db.add(attendance_record)
    db.commit()

    return schemas.FaceRecognizeResult(
        matched=True,
        student_id=student.id,
        student_name=student.full_name,
        roll_number=student.roll_number,
        confidence=attendance_record.confidence,
        status=status_flag,
        message=f"Attendance Verified! Marked as {status_flag} for {student.full_name}"
    )

@router.post("/manual", response_model=schemas.AttendanceOut)
def mark_manual_attendance(
    log_data: schemas.AttendanceLogRequest,
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.get_current_admin)
):
    student = db.query(models.Student).filter(models.Student.id == log_data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    rec = models.Attendance(
        student_id=student.id,
        class_id=log_data.class_id,
        date=log_data.date,
        time=log_data.time,
        status=log_data.status,
        confidence=1.0,
        verified_by=f"Admin ({admin.full_name})"
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {
        "id": rec.id,
        "student_id": rec.student_id,
        "student_name": student.full_name,
        "roll_number": student.roll_number,
        "department_name": student.department.name if student.department else "-",
        "class_id": rec.class_id,
        "date": rec.date,
        "time": rec.time,
        "status": rec.status,
        "confidence": rec.confidence,
        "verified_by": rec.verified_by
    }
