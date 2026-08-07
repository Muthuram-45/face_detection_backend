import io
import csv

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

def generate_pdf_report(records: list[dict], title: str = "Attendance Report") -> bytes:
    if HAS_REPORTLAB:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        story = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=12
        )
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 10))

        headers = ["Roll No", "Student Name", "Department", "Date", "Time", "Status"]
        table_data = [headers]

        for r in records:
            table_data.append([
                str(r.get("roll_number", "")),
                str(r.get("student_name", "")),
                str(r.get("department_name", "")),
                str(r.get("date", "")),
                str(r.get("time", "")),
                str(r.get("status", ""))
            ])

        t = Table(table_data, colWidths=[80, 130, 110, 80, 70, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F8FAFC')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
        ]))
        
        story.append(t)
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    else:
        # Fallback text representation if reportlab is not installed
        content = f"{title}\n" + "="*40 + "\n"
        content += "Roll No | Student Name | Department | Date | Time | Status\n"
        for r in records:
            content += f"{r.get('roll_number')} | {r.get('student_name')} | {r.get('department_name')} | {r.get('date')} | {r.get('time')} | {r.get('status')}\n"
        return content.encode("utf-8")

def generate_excel_report(records: list[dict]) -> bytes:
    if HAS_OPENPYXL:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Attendance Summary"

        headers = ["Roll Number", "Student Name", "Department", "Date", "Time", "Status", "Confidence", "Verified By"]
        ws.append(headers)

        for r in records:
            ws.append([
                r.get("roll_number", ""),
                r.get("student_name", ""),
                r.get("department_name", ""),
                r.get("date", ""),
                r.get("time", ""),
                r.get("status", ""),
                f"{r.get('confidence', 0) * 100:.1f}%",
                r.get("verified_by", "AI Camera")
            ])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
    else:
        return generate_csv_report(records).encode("utf-8")

def generate_csv_report(records: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Roll Number", "Student Name", "Department", "Date", "Time", "Status", "Confidence"])
    for r in records:
        writer.writerow([
            r.get("roll_number", ""),
            r.get("student_name", ""),
            r.get("department_name", ""),
            r.get("date", ""),
            r.get("time", ""),
            r.get("status", ""),
            f"{r.get('confidence', 0) * 100:.1f}%"
        ])
    return output.getvalue()
