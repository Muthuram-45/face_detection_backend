from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/notifications", tags=["Notifications & Alerts"])

@router.get("", response_model=List[schemas.NotificationOut])
def get_notifications(db: Session = Depends(get_db)):
    return db.query(models.Notification).order_by(models.Notification.id.desc()).limit(20).all()

@router.post("/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    notif = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"message": "Notification marked as read"}

@router.get("/unknown-faces")
def get_unknown_faces(db: Session = Depends(get_db)):
    return db.query(models.UnknownFace).order_by(models.UnknownFace.id.desc()).limit(20).all()

@router.post("/unknown-faces/{face_id}/resolve")
def resolve_unknown_face(face_id: int, action: str = "Dismissed", db: Session = Depends(get_db)):
    face = db.query(models.UnknownFace).filter(models.UnknownFace.id == face_id).first()
    if face:
        face.status = action
        db.commit()
    return {"message": f"Unknown face status updated to {action}"}
