"""
Export Service
Handles data export to CSV, Excel, and PDF formats
"""
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import os
from datetime import datetime

class ExportService:
    
    @staticmethod
    def to_csv(data, filename_prefix="export"):
        """Export data list to CSV"""
        try:
            df = pd.DataFrame(data)
            output = BytesIO()
            df.to_csv(output, index=False)
            output.seek(0)
            return output, f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv"
        except Exception as e:
            raise Exception(f"CSV Export failed: {str(e)}")

    @staticmethod
    def to_excel(data, filename_prefix="export"):
        """Export data list to Excel"""
        try:
            df = pd.DataFrame(data)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            output.seek(0)
            return output, f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        except Exception as e:
            raise Exception(f"Excel Export failed: {str(e)}")

    @staticmethod
    def to_pdf(data, title="Report", filename_prefix="export"):
        """Export data list to PDF"""
        try:
            output = BytesIO()
            doc = SimpleDocTemplate(output, pagesize=landscape(letter))
            elements = []
            styles = getSampleStyleSheet()

            # Title
            elements.append(Paragraph(title, styles['Title']))
            elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 20))

            if not data:
                elements.append(Paragraph("No data available", styles['Normal']))
            else:
                # Table Data
                headers = list(data[0].keys())
                table_data = [headers]
                
                for row in data:
                    table_data.append([str(row.get(h, '')) for h in headers])

                # Table Style
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)

            doc.build(elements)
            output.seek(0)
            return output, f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", "application/pdf"
            
        except Exception as e:
            raise Exception(f"PDF Export failed: {str(e)}")
