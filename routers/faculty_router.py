from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/faculty", tags=["Faculty"])

@router.get("")
def get_faculty_list(db: Session = Depends(get_db)):
    faculties = db.query(models.Faculty).all()
    res = []
    for f in faculties:
        res.append({
            "id": f.id,
            "employee_code": f.employee_code,
            "full_name": f.full_name,
            "email": f.email,
            "department_id": f.department_id,
            "department_name": f.department.name if f.department else "Unassigned",
            "created_at": f.created_at
        })
    return res

@router.post("")
def create_faculty(
    employee_code: str,
    full_name: str,
    email: str,
    department_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.get_current_admin)
):
    existing = db.query(models.Faculty).filter(models.Faculty.employee_code == employee_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Faculty employee code already exists")

    # Create faculty user login account
    user = models.User(
        email=email,
        hashed_password=auth.get_password_hash("faculty123"),
        full_name=full_name,
        role="faculty"
    )
    db.add(user)
    db.flush()

    faculty = models.Faculty(
        user_id=user.id,
        employee_code=employee_code,
        full_name=full_name,
        email=email,
        department_id=department_id
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty
