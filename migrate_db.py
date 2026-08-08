import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

import sys
sys.stdout.reconfigure(line_buffering=True)

NEON_URL = "postgresql://neondb_owner:npg_jI4qASCK8JoY@ep-green-firefly-axvthrzd-pooler.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
SUPA_URL = "postgresql://postgres.qpwqyvtozuxpgbkkobnp:muthuram921@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require"

print("Initializing engines...")
engine_neon = create_engine(NEON_URL)
engine_supa = create_engine(SUPA_URL)

SessionNeon = sessionmaker(bind=engine_neon)
SessionSupa = sessionmaker(bind=engine_supa)

def migrate_data():
    print("Creating tables in Supabase...")
    models.Base.metadata.create_all(bind=engine_supa)
    
    neon_db = SessionNeon()
    supa_db = SessionSupa()
    
    try:
        # Define the order of tables to respect foreign keys
        tables_to_migrate = [
            models.Department,
            models.User,
            models.Faculty,
            models.ClassRoom,
            models.Student,
            models.AttendanceSession,
            models.FaceEmbedding,
            models.Attendance,
            models.UnknownFace,
            models.Notification,
            models.SystemSetting
        ]
        
        for table in tables_to_migrate:
            print(f"Migrating {table.__tablename__}...")
            records = neon_db.query(table).all()
            if records:
                # We need to detach them from the old session to insert into the new one
                for r in records:
                    supa_db.merge(r)
                supa_db.commit()
                print(f"Migrated {len(records)} records for {table.__tablename__}.")
            else:
                print(f"No records found for {table.__tablename__}.")
        
        print("Migration complete!")
        
    except Exception as e:
        supa_db.rollback()
        print(f"Error during migration: {e}")
    finally:
        neon_db.close()
        supa_db.close()

if __name__ == "__main__":
    migrate_data()
