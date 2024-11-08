import io
from django.http import FileResponse
from django.shortcuts import render
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from myapp.service import *
from .es import *
import json
from django.utils import timezone
from django.db import connections
from datetime import datetime
from django.utils.timezone import make_aware
from django.urls import reverse
import ipaddress

def truncate_text(text, max_length):
    return text if len(text) <= max_length else text[:max_length] + '...'

def categorize(value):
        if value is None:  
            return 'N/A'  
        if value <= 30:
            return '하 (30% 이하)'
        elif value <= 70:
            return '중 (70% 이하)'
        else:
            return '상 (70% 초과)'

##############################

def test_view(request, instance_id, reportType, start_date, end_date):


    print("@@@@@@@@@@@@@@@@@test@@@@@@@@@@@@@@@")

    start_date_obj_pre = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj_pre = datetime.strptime(end_date, "%Y-%m-%d")

    start_date_obj = timezone.make_aware(start_date_obj_pre, timezone.get_current_timezone())
    end_date_obj = timezone.make_aware(end_date_obj_pre.replace(hour=23, minute=59, second=59, microsecond=999999), timezone.get_current_timezone())

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
            i.uuid 
        FROM 
            instances i 
        JOIN 
            block_device_mapping b 
        ON 
            i.id = b.id
        WHERE 
            i.id = %s;
    '''
    
    with connections['mariadb_nova'].cursor() as cursor:
        cursor.execute(query, [instance_id])
        rows = cursor.fetchall()
    
    data = []
    current_time = timezone.now()

    for row in rows:

        updated_at = row[5]

        if updated_at.tzinfo is None:
            updated_at = make_aware(updated_at)

        uptime = current_time - updated_at
        days = uptime.days
        hours = (uptime.seconds // 3600) % 24
        minutes = (uptime.seconds // 60) % 60 
        formatted_uptime = f"{days} days, {hours}:{minutes}"

        data.append({
            'id': row[0],
            'display_name': row[1],
            'created_at': row[2],
            'host': row[3],
            'hostname': row[4],
            'uptime': formatted_uptime,
            'root_device_name': row[6],
            'vcpus': row[7],
            'memory_mb': row[8],
            'instance_uuid': row[9],
        })
    instance_data = data[0]

    ip_mapping_query = get_report_ip_mapping(row[9])
    ip_addresses = []

    for entry in ip_mapping_query:
        if entry.get('ip_address'):
            ip_addresses.extend(entry['ip_address']) 

    if not ip_addresses:
        ip_addresses = ['']

    ip_addresses_str = ', '.join(ip_addresses)
    report_type_query = get_report_type(reportType)
        
    if report_type_query:
        for item in report_type_query:
            engineName = item['engine_name']  
            engineInfo = item['engine_info']
###################################### 보고서 #########################################

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
    title = "서버 점검 리포트"
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.fontName = 'font'
    title_style.fontSize = 20
    title_style.alignment = 1
    title_style.spaceAfter = 20 
    elements.append(Paragraph(title, title_style))

    date_data = [
        ['IP',  ip_addresses_str]
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

    if len(instance_data['display_name']) > 23:  
        displayName = '...' + instance_data['display_name'][-21:]
    else:
        displayName = instance_data['display_name']

    # Draw the equipment details table in the desired format
    equipment_data = [
        ['날짜', start_date + "~" + end_date, 'Uptime', formatted_uptime],
        ['호스트명', displayName, '컨트롤러', instance_data['host']],
        ['image', 'ubuntu', '장치', instance_data['root_device_name']],
        ['VCPU', instance_data['vcpus'], 'MEMORY(mb)', instance_data['memory_mb']],
    ]
    # Adjust column widths to fit the page width
    equipment_col_width = (doc.pagesize[0] - 2 * 72) / 4  # Divide by the number of columns
    equipment_table = Table(equipment_data, colWidths=[equipment_col_width] * 4)
    equipment_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONT', (0, 0), (-1, -1), 'font'),
        ('FONTNAME', (0, 0), (-1, -1), 'font'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid linesF
        ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Increase bottom padding
    ]))
    elements.append(equipment_table)

    ############################  추후 모니터링용 대역으로 변경 필요  #####################################
    target_network = ipaddress.ip_network("192.168.0.0/24")
    filtered_ips = [
        ip for ip in ip_addresses 
        if ip not in ['0', '0.0.0.0'] and ip and ipaddress.ip_address(ip) in target_network
    ]

    # selected_ip를 초기화
    selected_ip = None

    if filtered_ips:
        selected_ip = filtered_ips[0] + ':8088' 
    else:
        selected_ip = None  
  
    if selected_ip:
        print("#### avg fetch")
        print("start: ")
        print(datetime.now())
        avg_cpu_usage, avg_mem_usage, avg_disk_size, avg_disk_used = get_resource_usage_averages(selected_ip, start_date_obj, end_date_obj)
        print("end: ")
        print(datetime.now())

        if avg_disk_size is not None and avg_disk_size > 0:
            disk_usage_percentage = categorize(avg_disk_used / avg_disk_size)
            avg_disk_size_gb = round(avg_disk_size / 1024, 1)
            avg_disk_used_gb = round(avg_disk_used / 1024, 1)
        else:
            disk_usage_percentage = categorize(None)
        
        resource_data = [
            ['자원사용량 요약']
        ]

        # Adjust column widths to fit the page width
        resource_table = Table(resource_data, colWidths=[equipment_col_width * 4])
        resource_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONT', (0, 0), (-1, -1), 'font'),
            ('FONTSIZE', (0, 0), (-1, -1), 13),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),  # Increase bottom padding
        ]))
        elements.append(resource_table)

        ip_suffix = selected_ip.split(':')[0].split('.')[-1]
        today_date = datetime.now().strftime("%Y.%m")
        index_pattern = f"{ip_suffix}syslog_logs_{today_date}*"

        print("#### log fetch")
        print("start: ")
        print(datetime.now())
        log_levels_buckets = fetch_log_levels_for_date_range(selected_ip, start_date_obj, end_date_obj)
        print("end: ")
        print(datetime.now())
       
        date_diff = (end_date_obj.date() - start_date_obj.date()).days
            
        for engines in engineInfo:
            print("#### engine")
            print("start: ")
            print(datetime.now())
            engineCount, engineOn5m = get_count_for_command(engines, selected_ip, start_date_obj, end_date_obj)
            print("end: ")
            print(datetime.now())
       
            if len(engines) > 80:
                engines = '...' + engines[-77:]

            if (engineCount > (1400 * (date_diff + 1))) & engineOn5m:
                engineStatus = '정상'
            else:
                engineStatus = "비정상"

            print(date_diff)
            print(engineCount)
            print(1400 * (date_diff + 1))
            print(engineOn5m)
        if avg_cpu_usage is not None:   
            print("#### cpu5 fetch")
            print("start: ")
            print(datetime.now())
            top_cpu_usages = get_process_cpu_usage_top5(selected_ip, start_date_obj, end_date_obj)
            print("end: ")
            print(datetime.now())
            print("#### mem5 fetch")
            print("start: ")
            print(datetime.now())
            top_mem_usages = get_process_mem_usage_top5(selected_ip, start_date_obj, end_date_obj)
            print("end: ")
            print(datetime.now())
            print("#### port fetch")
            print("start: ")
            print(datetime.now())
            top_port_usages = get_unique_port_usage(selected_ip, start_date_obj, end_date_obj)
            print("end: ")
            print(datetime.now())

    # Build PDF
    doc.build(elements)

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    pdf = buffer.getvalue()
    buffer.close()

    response = FileResponse(io.BytesIO(pdf), as_attachment=True, filename='instance_report.pdf')
    return response