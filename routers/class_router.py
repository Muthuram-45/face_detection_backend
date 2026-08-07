from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/classes", tags=["Classes"])

@router.get("", response_model=List[schemas.ClassRoomOut])
def get_classes(db: Session = Depends(get_db)):
    return db.query(models.ClassRoom).all()

@router.post("", response_model=schemas.ClassRoomOut)
def create_class(
    class_data: schemas.ClassRoomCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.get_current_admin)
):
    cls = models.ClassRoom(**class_data.model_dump())
    db.add(cls)
    db.flush()

    # Automatically activate an AttendanceSession matching the created Class details
    from datetime import datetime
    sched = cls.schedule_time or ""
    start_t, end_t = sched, "10:00 AM"
    for delim in [" to ", " - ", "-"]:
        if delim in sched.lower():
            parts = sched.lower().split(delim)
            start_t, end_t = parts[0].strip(), parts[1].strip()
            break

    sess = models.AttendanceSession(
        title=f"{cls.name} Session",
        faculty_name=cls.faculty_name,
        subject_code=cls.subject_code,
        department_id=cls.department_id,
        year=None,
        section=None,
        date=datetime.now().strftime("%Y-%m-%d"),
        start_time=start_t or "09:00 AM",
        end_time=end_t or "10:00 AM",
        status="Active"
    )
    db.add(sess)
    db.commit()
    db.refresh(cls)
    return cls

@router.delete("/{class_id}")
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.get_current_admin)
):
    cls = db.query(models.ClassRoom).filter(models.ClassRoom.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Close any active attendance sessions for this subject
    db.query(models.AttendanceSession).filter(
        models.AttendanceSession.subject_code == cls.subject_code
    ).update({"status": "Completed"})

    db.delete(cls)
    db.commit()
    return {"message": "Class deleted and associated sessions closed"}
