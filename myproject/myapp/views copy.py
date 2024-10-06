import io
import os
from django.http import FileResponse
from django.shortcuts import render
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from .service import *
from django.conf import settings
import json
from django.core.files.storage import default_storage
from django.utils import timezone
from django.db import connections
from datetime import datetime
from django.utils.timezone import make_aware
from django.urls import reverse

############################## 테스트


    
def home_view(request):

    current_time = timezone.now()

    query = '''
        SELECT 
            i.id, 
            i.display_name, 
            i.created_at,
            i.host,
            i.hostname,
            i.updated_at,
            i.root_device_name,
            i.vcpus,
            i.memory_mb,
            b.instance_uuid 
        FROM 
            instances i 
        JOIN 
            block_device_mapping b 
        ON 
            i.id = b.id;
    '''

    with connections['mariadb_nova'].cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    with open('/monitoring/targets.json') as f:
        targets = json.load(f)

    data = []
    for row in rows:
        updated_at = row[5]

        if updated_at.tzinfo is None:
            updated_at = make_aware(updated_at)

        uptime = current_time - updated_at
        days = uptime.days
        hours = (uptime.seconds // 3600) % 24
        minutes = (uptime.seconds // 60) % 60 
        formatted_uptime = f"{days} days, {hours}:{minutes}"

        ip_addresses = [target['ip'] for target in targets if target['name'] == row[4]]
        ip_addresses_str = ', '.join(ip_addresses)

        data.append({
            'id': row[0],
            'display_name': row[1],
            'created_at': row[2],
            'host': row[3],
            'hostname': row[4],
            'uptime': formatted_uptime,
            'device': row[6],
            'vcpus': row[7],
            'memory_mb': row[8],
            'instance_uuid': row[9],
            'image': "ubuntu",
            'ip_addresses': ip_addresses_str,
            'pdf_url': reverse('some_view', args=[row[0]])
        })
    

    return render(request, 'index.html', {'data': data})


##############################

def truncate_text(text, max_length):
    return text if len(text) <= max_length else text[:max_length] + '...'

def categorize(value):
        if value is None:  
            return 'N/A'  
        if value <= 30:
            return '하'
        elif value <= 70:
            return '중'
        else:
            return '상'
        
########################################################################################################### 보고서

def some_view(request, instance_id):
    
    
    file_path = os.path.join(settings.BASE_DIR, 'targets.json')  # Update this to the correct file path

    # # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()   

    # # Create the PDF object, using the buffer as its "file."
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            rightMargin=72, leftMargin=72, 
                            topMargin=50, bottomMargin=50)
    elements = []

    # # Register the font
    pdfmetrics.registerFont(TTFont('font', '조선굴림체.TTF'))

    # # Title
    title = "서버 정기 점검 일지"
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.fontName = 'font'
    title_style.fontSize = 20
    title_style.alignment = 1
    title_style.spaceAfter = 20 
    elements.append(Paragraph(title, title_style))

    now = datetime.now()
    date_str = now.strftime('%Y년 %m월 %d일 %I:%M')

#     # Draw the date information in a table
    date_data = [
        ['IP', instance_id]
    ]
#     # Adjust column widths to fit the page width
    page_width = doc.pagesize[0] - 2 * 72  # Page width minus margins
    date_table = Table(date_data, colWidths=[page_width / 4, page_width * 3 / 4])
    date_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONT', (0, 0), (-1, -1), 'font'),
        ('FONTNAME', (0, 0), (-1, -1), 'font'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),  # Change background to white
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid lines
        ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Increase bottom padding
    ]))
    elements.append(date_table)

#     # Draw the equipment details table in the desired format
#     equipment_data = [
#         ['날짜', date_str, 'Uptime', '11일 11시간'],
#         ['호스트명', 'host', '컨트롤러', 'con'],
#         ['image', 'm1', '장치', '/dev/vda'],
#         ['VCPU', '1', 'MEMORY', 'GB'],
#     ]
#     # Adjust column widths to fit the page width
#     equipment_col_width = (doc.pagesize[0] - 2 * 72) / 4  # Divide by the number of columns
#     equipment_table = Table(equipment_data, colWidths=[equipment_col_width] * 4)
#     equipment_table.setStyle(TableStyle([
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONT', (0, 0), (-1, -1), 'font'),
#         ('FONTNAME', (0, 0), (-1, -1), 'font'),
#         ('FONTSIZE', (0, 0), (-1, -1), 10),
#         ('BACKGROUND', (0, 0), (-1, 0), colors.white),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid lines
#         ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
#         ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Increase bottom padding
#     ]))
#     elements.append(equipment_table)

#     avg_cpu_usage, avg_mem_usage, avg_disk_size, avg_disk_used = get_resource_usage_averages(instance_ip)

#     process_style = styles['Normal']
#     process_style.fontName = 'font'
#     process_style.fontSize = 12
#     process_style.leading = 12  # Line height
#     process_style.spaceBefore = 10
#     process_style.spaceAfter = 10  # Space after paragraph
#     process_style.alignment = 1  # Center-align text

#     text_between_tables = Paragraph("자원사용 위험도", process_style)
#     elements.append(text_between_tables)

#     resource_data = [
#         ['CPU', categorize(avg_cpu_usage)],  # 두 번째 줄: 1칸과 3칸 크기로 나누어 배치
#         ['MEM', categorize(avg_mem_usage)],  # 세 번째 줄: 1칸과 3칸 크기로 나누어 배치
#         ['DISK', categorize(avg_disk_used/avg_disk_size)]
#     ]

#     # Adjust column widths to fit the page width
#     resource_table = Table(resource_data, colWidths=[equipment_col_width, equipment_col_width * 3])
#     resource_table.setStyle(TableStyle([
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONT', (0, 0), (-1, -1), 'font'),
#         ('FONTSIZE', (0, 1), (-1, -1), 10),
#         ('BACKGROUND', (0, 0), (-1, 0), colors.white),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),
#         ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
#         ('BOTTOMPADDING', (0, 1), (-1, -1), 6),  # Increase bottom padding
#     ]))
#     elements.append(resource_table)


#     process_style = styles['Normal']
#     process_style.fontName = 'font'
#     process_style.fontSize = 12
#     process_style.leading = 12  # Line height
#     process_style.spaceBefore = 10
#     process_style.spaceAfter = 10  # Space after paragraph
#     process_style.alignment = 1  # Center-align text

#     text_between_tables = Paragraph("주요 프로세스", process_style)
#     elements.append(text_between_tables)

#     resource_data = [
#         ['주요1', '11'],  
#         ['주요2', '22'], 
#         ['주요3', '33'],
#         ['주요4', '44'],
#         ['주요5', '55']
#     ]

#     main_process_table = Table(resource_data, colWidths=[equipment_col_width, equipment_col_width * 3])
#     main_process_table.setStyle(TableStyle([
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONT', (0, 0), (-1, -1), 'font'),
#         ('FONTSIZE', (0, 1), (-1, -1), 10),
#         ('BACKGROUND', (0, 0), (-1, 0), colors.white),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),
#         ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
#         ('BOTTOMPADDING', (0, 1), (-1, -1), 6),  # Increase bottom padding
#     ]))
#     elements.append(main_process_table)


#     elements.append(PageBreak())

# ################################################################################################################################ 다음페이지
#     process_style = styles['Normal']
#     process_style.fontName = 'font'
#     process_style.fontSize = 12
#     process_style.leading = 12  # Line height
#     process_style.spaceBefore = 10
#     process_style.spaceAfter = 10  # Space after paragraph
#     process_style.alignment = 1  # Center-align text

#     text_between_tables = Paragraph("자원사용량", process_style)
#     elements.append(text_between_tables)

#     # Resource Usage Table
#     resource_data = [
#         ['CPU', f'{avg_cpu_usage:.1f}%'],  # 두 번째 줄: 1칸과 3칸 크기로 나누어 배치
#         ['MEM', f'{avg_mem_usage:.1f}%'],  # 세 번째 줄: 1칸과 3칸 크기로 나누어 배치
#     ]

#     # Adjust column widths to fit the page width
#     resource_table = Table(resource_data, colWidths=[equipment_col_width, equipment_col_width * 3])
#     resource_table.setStyle(TableStyle([
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONT', (0, 0), (-1, -1), 'font'),
#         ('FONTSIZE', (0, 1), (-1, -1), 10),
#         ('BACKGROUND', (0, 0), (-1, 0), colors.white),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),
#         ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
#         ('BOTTOMPADDING', (0, 1), (-1, -1), 6),  # Increase bottom padding
#     ]))
#     elements.append(resource_table)

#     # Draw the DISK details table
#     disk_data = [
#         ['DISK', 'Mount', 'Size', 'Used', 'Avail', 'Use %'],
#         ['', '/', f'{avg_disk_size}G', f'{avg_disk_used}G', f'{avg_disk_size-avg_disk_used}G', f'{int((avg_disk_used/avg_disk_size)*100)}%']
#     ]

#     # Adjust column widths: 
#     # - DISK takes 1/4 of the width (same as previous single columns)
#     # - The remaining 3/4 is divided into 5 equal parts
#     disk_col_widths = [equipment_col_width] + [equipment_col_width * 3 / 5] * 5

#     disk_table = Table(disk_data, colWidths=disk_col_widths)
#     disk_table.setStyle(TableStyle([
#         ('SPAN', (0, 0), (0, 1)),  # DISK spans across two rows
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('VALIGN', (0, 0), (0, 1), 'MIDDLE'),
#         ('FONT', (0, 0), (-1, -1), 'font'),
#         ('FONTNAME', (0, 0), (-1, -1), 'font'),
#         ('FONTSIZE', (0, 0), (-1, -1), 10),
#         ('BACKGROUND', (0, 0), (-1, -1), colors.white),
#         ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid lines
#         ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
#         ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Increase bottom padding
#     ]))
#     elements.append(disk_table)


#     process_style = styles['Normal']
#     process_style.fontName = 'font'
#     process_style.fontSize = 12
#     process_style.leading = 12  # Line height
#     process_style.spaceBefore = 10
#     process_style.spaceAfter = 10  # Space after paragraph
#     process_style.alignment = 1  # Center-align text

#     text_between_tables = Paragraph("프로세스 별 CPU 사용량 TOP 5", process_style)
#     elements.append(text_between_tables)

#     top_cpu_usages = get_process_cpu_usage_top5(instance_ip)

#     # Define the new table data
#     process_cpu_data = [
#         ['Command', 'PID', 'User', 'CPU%']
#     ]

#     for usage in top_cpu_usages:
#         process_cpu_data.append([
#             truncate_text(usage['command'], 20),
#             usage['pid'],
#             usage['instance_user'],
#             f"{usage['avg_cpu_usage']:.1f}"
#         ])

#     # Adjust column widths to fit the page width
#     new_table_col_width = (doc.pagesize[0] - 2 * 72) / 4  # Divide by the number of columns
#     new_table = Table(process_cpu_data, colWidths=[new_table_col_width] * 2)
#     new_table.setStyle(TableStyle([
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONT', (0, 0), (-1, -1), 'font'),
#         ('FONTNAME', (0, 0), (-1, -1), 'font'),
#         ('FONTSIZE', (0, 0), (-1, -1), 10),
#         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid lines
#         ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
#         ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Increase bottom padding
#     ]))

#     # Add the new table to the elements list
#     elements.append(new_table)

#     text_between_tables = Paragraph("프로세스 별 MEM 사용량 TOP 5", process_style)
#     elements.append(text_between_tables)

#     top_mem_usages = get_process_mem_usage_top5(instance_ip)

#     # Define the new table data
#     process_mem_data = [
#         ['Command', 'PID', 'User', 'MEM%']
#     ]

#     for usage in top_mem_usages:
#         process_mem_data.append([
#             truncate_text(usage['command'], 20),
#             usage['pid'],
#             usage['instance_user'],
#             f"{usage['avg_mem_usage']:.1f}"
#         ])

#     # Adjust column widths to fit the page width
#     new_table_col_width = (doc.pagesize[0] - 2 * 72) / 4  # Divide by the number of columns
#     new_table = Table(process_mem_data, colWidths=[new_table_col_width] * 2)
#     new_table.setStyle(TableStyle([
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONT', (0, 0), (-1, -1), 'font'),
#         ('FONTNAME', (0, 0), (-1, -1), 'font'),
#         ('FONTSIZE', (0, 0), (-1, -1), 10),
#         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid lines
#         ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
#         ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Increase bottom padding
#     ]))

#     # Add the new table to the elements list
#     elements.append(new_table)
#     elements.append(PageBreak())


# ########################################################################################################################### 보고서


    # Build PDF
    doc.build(elements)

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    pdf = buffer.getvalue()
    buffer.close()

    response = FileResponse(io.BytesIO(pdf), as_attachment=True, filename='instance_report.pdf')
    return response