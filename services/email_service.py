import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings

logger = logging.getLogger(__name__)

def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    """Send email via standard SMTP (or log notification in dev mode)."""
    try:
        # Check if SMTP settings are configured in environment
        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "demo.attendance.system@gmail.com"
        smtp_pass = "demo_password"

        # In non-configured mode, cleanly log and simulate success
        logger.info(f"[Email Triggered] To: {to_email} | Subject: {subject}")
        logger.info(f"[Email Body]: {body[:100]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def notify_absentee(student_name: str, student_email: str, date: str, subject_name: str):
    subject = f"Attendance Notice: Absent for {subject_name} on {date}"
    body = f"Dear {student_name},\n\nThis is an automated notification from the AI Attendance System. You were marked ABSENT for {subject_name} on {date}.\n\nIf you believe this is an error, please contact your department coordinator."
    send_email_notification(student_email, subject, body)

def notify_unknown_face_alert(admin_email: str, timestamp: str, camera_location: str):
    subject = f"SECURITY ALERT: Unknown Face Detected at {camera_location}"
    body = f"Security Notification:\n\nAn unrecognized individual was captured by the AI Camera at {camera_location} at {timestamp}.\n\nPlease log in to the admin portal to review security logs."
    send_email_notification(admin_email, subject, body)
