# report_generator.py
import os
from datetime import datetime
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class PDFReportGenerator:
    """
    Generate a PDF report for a body fat analysis
    """
    def __init__(self, base_output_dir="reports"):
        self.base_output_dir = base_output_dir
        os.makedirs(self.base_output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Default value style
        self.style_value = self.styles['Normal']
        self.style_value.fontSize = 10
        self.style_value.leading = 12
        
        # Large text style
        self.style_large = self.styles['Normal']
        self.style_large.fontSize = 16
        self.style_large.leading = 18
        
        # Header style for tables (smaller font)
        self.style_header_small = ParagraphStyle(
            name='HeaderSmall',
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=12,
            alignment=1  # center
        )

    def generate_report(self, student_info: dict, analysis_result: dict, raw_image_path: str, annotated_image_path: str):
        student_id = student_info.get("student_id") or "Unknown"

        # --- Create student folder ---
        student_folder = os.path.join(self.base_output_dir, student_id)
        os.makedirs(student_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = os.path.join(student_folder, f"report_{timestamp}.pdf")

        # Optional: also move images to the same folder
        raw_dest = os.path.join(student_folder, os.path.basename(raw_image_path))
        annotated_dest = os.path.join(student_folder, os.path.basename(annotated_image_path))
        os.replace(raw_image_path, raw_dest)
        os.replace(annotated_image_path, annotated_dest)

        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        margin = 50
        content_width = width - 2 * margin

        # --- Title ---
        c.setFont("Helvetica-Bold", 26)
        c.drawCentredString(width / 2, height - 50, "FATCHECK")
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 80, "Body Fat Analysis")
        c.line(margin, height - 90, width - margin, height - 90)

        y_position = height - 105

        # --- Student Info Table ---
        headers = ["Name", "Age", "Gender", "Student ID", "Grade Level", "Section"]
        values = [
            student_info.get("name", "N/A"),
            str(student_info.get("age", "N/A")),
            student_info.get("gender", "N/A"),
            student_info.get("student_id", "N/A"),
            student_info.get("grade_name", "N/A"),
            student_info.get("section_name", "N/A")
        ]

        style_wrapped = ParagraphStyle(
            name='Wrapped',
            fontName='Helvetica',
            fontSize=10,
            leading=12,
            wordWrap='LTR'
        )

        data = [
            [Paragraph(h, self.style_header_small) for h in headers],  # header row
            [Paragraph(v, style_wrapped) for v in values]
        ]

        fixed_widths = [65, 70, 80, 70, 50]
        remaining_width = content_width - sum(fixed_widths)
        col_widths = [remaining_width] + fixed_widths

        student_table = Table(data, colWidths=col_widths)
        student_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('ALIGN', (0,1), (0,1), 'LEFT'),
            ('ALIGN', (1,1), (1,1), 'CENTER'),
            ('ALIGN', (2,1), (2,1), 'CENTER'),
            ('ALIGN', (3,1), (3,1), 'CENTER'),
            ('ALIGN', (4,1), (4,1), 'CENTER'),
            ('ALIGN', (5,1), (5,1), 'CENTER'),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
        ]))

        w, h = student_table.wrapOn(c, content_width, y_position)
        student_table.drawOn(c, margin, y_position - h)
        y_position -= h + 40

        # --- Analysis Result ---
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, y_position, "Analysis Result")
        y_position -= 30

        measurements = analysis_result.get("measurements", {})
        bfp = round(analysis_result.get("body_fat_percent", 0))
        category = analysis_result.get("category", "N/A")

        c.setFont("Helvetica", 14)
        c.drawString(margin, y_position, "Estimated Body Fat %: ")
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin + 180, y_position, f"{bfp}%")
        y_position -= 25

        c.setFont("Helvetica", 14)
        c.drawString(margin, y_position, "Category: ")
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin + 180, y_position, category)
        y_position -= 35

        # --- Metrics Table ---
        analysis_headers = ["Metric", "Value"]
        analysis_values = [
            ("Estimated Height (cm)", str(round(measurements.get("Estimated Height (cm)", 0)))),
            ("Estimated Weight (kg)", str(round(measurements.get("Estimated Weight (kg)", 0)))),
            ("Waist Circumference (cm)", str(round(measurements.get("Waist Circumference (cm)", 0)))),
            ("Hip Circumference (cm)", str(round(measurements.get("Hip Circumference (cm)", 0)))),
            ("Neck Circumference (cm)", str(round(measurements.get("Neck Circumference (cm)", 0)))),
            ("Chest Circumference (cm)", str(round(measurements.get("Chest Circumference (cm)", 0))))
        ]

        analysis_data = [
            [Paragraph(h, self.style_header_small) for h in analysis_headers],
            *[[Paragraph(k, self.style_value), Paragraph(v, self.style_value)] for k,v in analysis_values]
        ]

        analysis_table = Table(analysis_data, colWidths=[250, 100])
        analysis_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('ALIGN', (0,1), (-1,-1), 'LEFT'),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
        ]))
        w, h = analysis_table.wrapOn(c, content_width, y_position)
        analysis_table.drawOn(c, (width - w)/2, y_position - h)
        y_position -= h + 20

        # --- Images ---
        max_img_width = (width - 120)/2
        max_img_height = 200
        x_left = margin
        x_right = x_left + max_img_width + 20
        img_y = y_position - max_img_height

        captions = ["Figure 1. Raw Image", "Figure 2. Processed Image"]

        for img_path, x, caption in zip([raw_dest, annotated_dest], [x_left, x_right], captions):
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    img_w, img_h = img.size
                    ratio = min(max_img_width / img_w, max_img_height / img_h)
                    img_w *= ratio
                    img_h *= ratio
                    c.drawImage(ImageReader(img), x, img_y, width=img_w, height=img_h)
                    c.setFont("Helvetica-Oblique", 10)
                    c.drawCentredString(x + img_w / 2, img_y - 12, caption)
                except Exception as e:
                    print("Error embedding image:", e)

        c.setFont("Helvetica-Oblique", 10)
        c.drawRightString(width - margin, 30, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        c.save()
        print(f"[PDFReportGenerator] Report saved to {pdf_path}")
        return pdf_path

