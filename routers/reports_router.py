from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
import models
from services.report_generator import generate_pdf_report, generate_excel_report, generate_csv_report

router = APIRouter(prefix="/reports", tags=["Reports Export"])

@router.get("/export")
def export_attendance_report(
    format: str = Query("pdf", pattern="^(pdf|excel|csv)$"),
    date: Optional[str] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Attendance).join(models.Student)
    if date:
        query = query.filter(models.Attendance.date == date)
    if department_id:
        query = query.filter(models.Student.department_id == department_id)

    logs = query.order_by(models.Attendance.date.desc()).all()
    
    records = [
        {
            "roll_number": l.student.roll_number if l.student else "-",
            "student_name": l.student.full_name if l.student else "Unknown",
            "department_name": l.student.department.name if l.student and l.student.department else "-",
            "date": l.date,
            "time": l.time,
            "status": l.status,
            "confidence": l.confidence,
            "verified_by": l.verified_by
        }
        for l in logs
    ]

    if format == "pdf":
        pdf_bytes = generate_pdf_report(records, title="AI Attendance Record Report")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=attendance_report.pdf"}
        )
    elif format == "excel":
        excel_bytes = generate_excel_report(records)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=attendance_report.xlsx"}
        )
    elif format == "csv":
        csv_str = generate_csv_report(records)
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=attendance_report.csv"}
        )
