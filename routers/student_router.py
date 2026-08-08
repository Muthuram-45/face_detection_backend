import os
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models, schemas, auth
from config import settings
from services.ai_client import ai_client

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("", response_model=List[schemas.StudentOut])
def get_students(
    department_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Student)
    if department_id:
        query = query.filter(models.Student.department_id == department_id)
    students = query.all()
    
    res = []
    for s in students:
        s_dict = schemas.StudentOut.model_validate(s).model_dump()
        s_dict["department_name"] = s.department.name if s.department else "Unassigned"
        res.append(s_dict)
    return res

@router.post("", response_model=schemas.StudentOut)
def create_student(
    student_data: schemas.StudentCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_faculty)
):
    """Faculty or Admin registers student and system auto-generates login account (Username = Roll Number)."""
    existing = db.query(models.Student).filter(models.Student.roll_number == student_data.roll_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student with this roll number already exists")

    # Auto-generate temporary initial password
    initial_password = f"TempPass_{student_data.roll_number[-4:]}"
    
    # Create associated student user login
    student_user = models.User(
        email=student_data.email,
        hashed_password=auth.get_password_hash("student123"), # Standard initial password
        full_name=student_data.full_name,
        role="student"
    )
    db.add(student_user)
    db.flush()

    student = models.Student(
        user_id=student_user.id,
        roll_number=student_data.roll_number,
        full_name=student_data.full_name,
        email=student_data.email,
        year=student_data.year,
        department_id=student_data.department_id
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    
    s_dict = schemas.StudentOut.model_validate(student).model_dump()
    s_dict["department_name"] = student.department.name if student.department else "Unassigned"
    return s_dict

@router.post("/{student_id}/upload-face")
async def upload_student_face_photos(
    student_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_faculty)
):
    """Faculty uploads 10-20 facial images for AI embedding generation and model retraining."""
    from config import supabase
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    saved_image_paths = []
    
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase Storage not configured.")

    for index, file in enumerate(files):
        ext = os.path.splitext(file.filename)[1] or ".jpg"
        filename = f"student_{student_id}_{uuid.uuid4().hex[:8]}{ext}"
        storage_path = f"{student_id}/{filename}"
        
        content = await file.read()
        
        # Upload to Supabase Storage bucket 'students'
        res = supabase.storage.from_("students").upload(
            file=content,
            path=storage_path,
            file_options={"content-type": file.content_type or "image/jpeg"}
        )
        
        # Get public URL
        public_url = supabase.storage.from_("students").get_public_url(storage_path)
        saved_image_paths.append(public_url)
        
        if index == 0:
            student.photo_url = public_url

    # Process face embeddings via AI client
    ai_res = ai_client.process_face_registration(student.id, saved_image_paths)
    
    # Store embedding record
    dummy_vec = [0.05 * (i % 10) for i in range(128)]
    embedding_rec = models.FaceEmbedding(
        student_id=student.id,
        embedding_data=json.dumps(dummy_vec),
        image_path=saved_image_paths[0]
    )
    db.add(embedding_rec)
    
    student.is_enrolled = True
    db.commit()

    return {
        "message": f"Successfully processed {len(files)} face images for {student.full_name}",
        "photo_url": student.photo_url,
        "ai_result": ai_res
    }

@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_faculty)
):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if student.user_id:
        user_rec = db.query(models.User).filter(models.User.id == student.user_id).first()
        if user_rec:
            db.delete(user_rec)
            
    db.delete(student)
    db.commit()
    return {"message": "Student deleted"}
