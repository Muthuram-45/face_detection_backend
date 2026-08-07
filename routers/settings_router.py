from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/settings", tags=["System Settings"])

@router.get("")
def get_settings(db: Session = Depends(get_db)):
    settings_recs = db.query(models.SystemSetting).all()
    res = {s.key: s.value for s in settings_recs}
    # Defaults if empty
    res.setdefault("late_threshold", "09:15")
    res.setdefault("confidence_threshold", "0.65")
    res.setdefault("email_notifications_enabled", "true")
    res.setdefault("smtp_host", "smtp.gmail.com")
    res.setdefault("camera_device_id", "0")
    return res

@router.post("")
def update_setting(
    setting_data: schemas.SettingUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.get_current_admin)
):
    setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == setting_data.key).first()
    if setting:
        setting.value = setting_data.value
    else:
        setting = models.SystemSetting(key=setting_data.key, value=setting_data.value)
        db.add(setting)
    db.commit()
    return {"message": f"Setting {setting_data.key} updated to {setting_data.value}"}
