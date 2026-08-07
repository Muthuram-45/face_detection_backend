import models
from database import engine, SessionLocal, Base

def reset_and_clean_database():
    """Wipes all demo/dummy student data, sample logs, and resets database to clean initial state."""
    db = SessionLocal()
    
    print("Clearing all demo attendance logs...")
    db.query(models.Attendance).delete()
    
    print("Clearing all demo face embeddings...")
    db.query(models.FaceEmbedding).delete()
    
    print("Clearing all demo unknown faces...")
    db.query(models.UnknownFace).delete()
    
    print("Clearing all demo notifications...")
    db.query(models.Notification).delete()

    print("Clearing all sample student records...")
    db.query(models.Student).delete()

    print("Clearing student login accounts...")
    db.query(models.User).filter(models.User.role == "student").delete()

    print("Clearing sample attendance sessions...")
    db.query(models.AttendanceSession).delete()

    db.commit()
    db.close()
    print("Database successfully wiped of all dummy demo data!")

if __name__ == "__main__":
    reset_and_clean_database()
