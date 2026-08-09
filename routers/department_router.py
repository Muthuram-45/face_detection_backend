from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.get("", response_model=List[schemas.DepartmentOut])
def get_departments(db: Session = Depends(get_db)):
    return db.query(models.Department).all()

@router.post("", response_model=schemas.DepartmentOut)
def create_department(
    dept_data: schemas.DepartmentCreate, 
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.get_current_admin)
):
    existing = db.query(models.Department).filter(
        (models.Department.code == dept_data.code) | (models.Department.name == dept_data.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department code or name already exists")
    
    dept = models.Department(**dept_data.model_dump())
    try:
        db.add(dept)
        db.commit()
        db.refresh(dept)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error while creating department")
    return dept

@router.delete("/{dept_id}")
def delete_department(
    dept_id: int, 
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.get_current_admin)
):
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    db.delete(dept)
    db.commit()
    return {"message": "Department deleted"}
