import json
from datetime import datetime, timedelta
from database import engine, Base, SessionLocal
import models
from auth import get_password_hash

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Check if Admin user exists
    admin = db.query(models.User).filter(models.User.email == "admin@attendance.ai").first()
    if not admin:
        admin = models.User(
            email="admin@attendance.ai",
            hashed_password=get_password_hash("admin123"),
            full_name="Dr. Robert Vance (Administrator)",
            role="admin"
        )
        db.add(admin)

    # 2. Add Departments
    dept_cs = db.query(models.Department).filter(models.Department.code == "CS").first()
    if not dept_cs:
        dept_cs = models.Department(name="Computer Science & Engineering", code="CS", description="Department of CS & AI")
        dept_ee = models.Department(name="Electrical & Electronics", code="EE", description="Department of Electrical Engineering")
        dept_me = models.Department(name="Mechanical Engineering", code="ME", description="Department of Mechanical Engineering")
        db.add_all([dept_cs, dept_ee, dept_me])
        db.flush()

    # 3. Add Classes
    cls1 = db.query(models.ClassRoom).filter(models.ClassRoom.subject_code == "CS301").first()
    if not cls1:
        cls1 = models.ClassRoom(name="Computer Vision & Deep Learning", subject_code="CS301", faculty_name="Prof. Sarah Jenkins", schedule_time="09:00 AM", department_id=dept_cs.id)
        cls2 = models.ClassRoom(name="Database Architecture", subject_code="CS302", faculty_name="Dr. Marcus Wright", schedule_time="11:00 AM", department_id=dept_cs.id)
        db.add_all([cls1, cls2])
        db.flush()

    # 3b. Add Faculty User
    fac_user = db.query(models.User).filter(models.User.email == "prof.sarah@university.edu").first()
    if not fac_user:
        fac_user = models.User(email="prof.sarah@university.edu", hashed_password=get_password_hash("faculty123"), full_name="Prof. Sarah Jenkins", role="faculty")
        db.add(fac_user)
        db.flush()
        
        fac_profile = models.Faculty(user_id=fac_user.id, employee_code="FAC-001", full_name="Prof. Sarah Jenkins", email="prof.sarah@university.edu", department_id=dept_cs.id)
        db.add(fac_profile)

    # 3c. Add Active Attendance Session
    sess1 = db.query(models.AttendanceSession).filter(models.AttendanceSession.subject_code == "CS301").first()
    if not sess1:
        sess1 = models.AttendanceSession(
            title="Morning CS301 Attendance Session",
            faculty_name="Prof. Sarah Jenkins",
            subject_code="CS301",
            date=datetime.now().strftime("%Y-%m-%d"),
            start_time="09:00 AM",
            end_time="10:00 AM",
            status="Active"
        )
        db.add(sess1)
        db.flush()

    # 4. Add Sample Enrolled Students
    s1 = db.query(models.Student).filter(models.Student.roll_number == "CS2026-001").first()
    if not s1:
        u1 = models.User(email="alex@student.edu", hashed_password=get_password_hash("student123"), full_name="Alex Morgan", role="student")
        db.add(u1)
        db.flush()
        
        s1 = models.Student(
            user_id=u1.id,
            roll_number="CS2026-001",
            full_name="Alex Morgan",
            email="alex@student.edu",
            year="3rd Year",
            department_id=dept_cs.id,
            photo_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400",
            is_enrolled=True
        )
        s2 = models.Student(
            roll_number="CS2026-002",
            full_name="Sophia Chen",
            email="sophia.c@university.edu",
            year="3rd Year",
            department_id=dept_cs.id,
            photo_url="https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400",
            is_enrolled=True
        )
        s3 = models.Student(
            roll_number="EE2026-015",
            full_name="David Miller",
            email="david.m@university.edu",
            year="2nd Year",
            department_id=dept_cs.id,
            photo_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
            is_enrolled=True
        )
        db.add_all([s1, s2, s3])
        db.flush()

        # Add face embeddings
        dummy_embedding = json.dumps([0.02 * i for i in range(128)])
        e1 = models.FaceEmbedding(student_id=s1.id, embedding_data=dummy_embedding)
        e2 = models.FaceEmbedding(student_id=s2.id, embedding_data=dummy_embedding)
        e3 = models.FaceEmbedding(student_id=s3.id, embedding_data=dummy_embedding)
        db.add_all([e1, e2, e3])

        # 5. Add Historical Attendance Logs
        today = datetime.now()
        for day_offset in range(5, -1, -1):
            d_str = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")
            att1 = models.Attendance(student_id=s1.id, class_id=cls1.id, date=d_str, time="08:58:12 AM", status="Present", confidence=0.96)
            att2 = models.Attendance(student_id=s2.id, class_id=cls1.id, date=d_str, time="09:18:45 AM" if day_offset % 2 == 0 else "08:55:00 AM", status="Late" if day_offset % 2 == 0 else "Present", confidence=0.94)
            att3 = models.Attendance(student_id=s3.id, class_id=cls1.id, date=d_str, time="09:02:10 AM", status="Present", confidence=0.91)
            db.add_all([att1, att2, att3])

    # 6. Add Initial System Settings
    late_setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == "late_threshold").first()
    if not late_setting:
        db.add(models.SystemSetting(key="late_threshold", value="09:15", description="Cutoff time for Late status marking"))
        db.add(models.SystemSetting(key="confidence_threshold", value="0.65", description="Minimum match confidence percentage"))
        db.add(models.SystemSetting(key="email_notifications_enabled", value="true", description="Enable automatic absentee notifications"))

    db.commit()
    db.close()
    print("Database successfully seeded with demo data!")

if __name__ == "__main__":
    seed_database()
