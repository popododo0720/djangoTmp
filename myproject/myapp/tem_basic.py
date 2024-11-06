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

def basic_view(request, instance_id, start_date, end_date):

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
            b.instance_uuid 
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

    ip_mapping_query = get_report_ip_mapping(row[1])
    ip_addresses = []

    for entry in ip_mapping_query:
        if entry.get('ip_address'):
            ip_addresses.extend(entry['ip_address']) 

    if not ip_addresses:
        ip_addresses = ['']

    ip_addresses_str = ', '.join(ip_addresses)

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
        avg_cpu_usage, avg_mem_usage, avg_disk_size, avg_disk_used = get_resource_usage_averages(selected_ip, start_date_obj, end_date_obj)
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


        resource_data = [
            ['CPU', categorize(avg_cpu_usage)],  # 두 번째 줄: 1칸과 3칸 크기로 나누어 배치
            ['MEM', categorize(avg_mem_usage)],  # 세 번째 줄: 1칸과 3칸 크기로 나누어 배치
            ['DISK', disk_usage_percentage]
        ]

        # Adjust column widths to fit the page width
        resource_table = Table(resource_data, colWidths=[equipment_col_width, equipment_col_width * 3])
        resource_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONT', (0, 0), (-1, -1), 'font'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),  # Increase bottom padding
        ]))
        elements.append(resource_table)

        process_style = styles['Normal']
        process_style.fontName = 'font'
        process_style.fontSize = 12
        process_style.leading = 12  # Line height
        process_style.spaceBefore = 10
        process_style.spaceAfter = 10  # Space after paragraph
        process_style.alignment = 1  # Center-align text

        
        ip_suffix = selected_ip.split(':')[0].split('.')[-1]
        today_date = datetime.now().strftime("%Y.%m")
        index_pattern = f"{ip_suffix}syslog_logs_{today_date}*"

        log_levels_buckets = fetch_log_levels(index_pattern)

        if log_levels_buckets: 
            filtered_log_levels = filter_log_levels(log_levels_buckets)

            resource_data = [
                ['로그 요약']
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

            resource_data = [
                ['로그 레벨', '카운트']
            ]
            for log in filtered_log_levels:
                resource_data.append([log['level'], str(log['count'])])

            main_process_table = Table(resource_data, colWidths=[equipment_col_width, equipment_col_width * 3])
            main_process_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONT', (0, 0), (-1, -1), 'font'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),  # Increase bottom padding
            ]))
            elements.append(main_process_table)

            # text_between_tables = Paragraph("주요 프로세스", process_style)
            # elements.append(text_between_tables)

            # resource_data = [
            #     ['주요1', '11'],  
            #     ['주요2', '22'], 
            #     ['주요3', '33'],
            #     ['주요4', '44'],
            #     ['주요5', '55']
            # ]

            # main_process_table = Table(resource_data, colWidths=[equipment_col_width, equipment_col_width * 3])
            # main_process_table.setStyle(TableStyle([
            #     ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            #     ('FONT', (0, 0), (-1, -1), 'font'),
            #     ('FONTSIZE', (0, 1), (-1, -1), 10),
            #     ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            #     ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            #     ('GRID', (0, 0), (-1, -1), 1, colors.black),
            #     ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
            #     ('BOTTOMPADDING', (0, 1), (-1, -1), 6),  # Increase bottom padding
            # ]))
            # elements.append(main_process_table)


        elements.append(PageBreak())

# ################################################################################################################################ 다음페이지
        if avg_cpu_usage is not None:    
            resource_data = [
                ['자원사용량']
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
            

            # Resource Usage Table
            resource_data = [
                ['CPU', f'{avg_cpu_usage:.1f}%'],  # 두 번째 줄: 1칸과 3칸 크기로 나누어 배치
                ['MEM', f'{avg_mem_usage:.1f}%'],  # 세 번째 줄: 1칸과 3칸 크기로 나누어 배치
            ]

            # Adjust column widths to fit the page width
            resource_table = Table(resource_data, colWidths=[equipment_col_width, equipment_col_width * 3])
            resource_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONT', (0, 0), (-1, -1), 'font'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),  # Increase bottom padding
            ]))
            elements.append(resource_table)

            # Draw the DISK details table
            disk_data = [
                ['DISK', 'Mount', 'Size', 'Used', 'Avail', 'Use %'],
                ['', '/', f'{avg_disk_size_gb}GB', f'{avg_disk_used_gb}GB', f'{round(avg_disk_size_gb - avg_disk_used_gb, 1)}GB', f'{int((avg_disk_used_gb/avg_disk_size_gb)*100)}%']
            ]

            # Adjust column widths: 
            # - DISK takes 1/4 of the width (same as previous single columns)
            # - The remaining 3/4 is divided into 5 equal parts
            disk_col_widths = [equipment_col_width] + [equipment_col_width * 3 / 5] * 5

            disk_table = Table(disk_data, colWidths=disk_col_widths)
            disk_table.setStyle(TableStyle([
                ('SPAN', (0, 0), (0, 1)),  # DISK spans across two rows
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (0, 1), 'MIDDLE'),
                ('FONT', (0, 0), (-1, -1), 'font'),
                ('FONTNAME', (0, 0), (-1, -1), 'font'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid lines
                ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Increase bottom padding
            ]))
            elements.append(disk_table)

            resource_data = [
                ['프로세스 별 CPU 사용량 TOP 5']
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

            top_cpu_usages = get_process_cpu_usage_top5(selected_ip, start_date_obj, end_date_obj)

            # Define the new table data
            process_cpu_data = [
                ['Command', 'PID', 'User', 'CPU%']
            ]

            for usage in top_cpu_usages:
                process_cpu_data.append([
                    truncate_text(usage['command'], 20),
                    usage['pid'],
                    usage['instance_user'],
                    f"{usage['avg_cpu_usage']:.1f}"
                ])

            # Adjust column widths to fit the page width
            new_table_col_width = (doc.pagesize[0] - 2 * 72) / 4  # Divide by the number of columns
            new_table = Table(process_cpu_data, colWidths=[new_table_col_width] * 2)
            new_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONT', (0, 0), (-1, -1), 'font'),
                ('FONTNAME', (0, 0), (-1, -1), 'font'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                # ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid lines
                ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Increase bottom padding
            ]))

            # Add the new table to the elements list
            elements.append(new_table)

            # text_between_tables = Paragraph("프로세스 별 MEM 사용량 TOP 5", process_style)
            # elements.append(text_between_tables)

            resource_data = [
                ['프로세스 별 MEM 사용량 TOP 5']
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

            top_mem_usages = get_process_mem_usage_top5(selected_ip, start_date_obj, end_date_obj)

            # Define the new table data
            process_mem_data = [
                ['Command', 'PID', 'User', 'MEM%']
            ]

            for usage in top_mem_usages:
                process_mem_data.append([
                    truncate_text(usage['command'], 20),
                    usage['pid'],
                    usage['instance_user'],
                    f"{usage['avg_mem_usage']:.1f}"
                ])

            # Adjust column widths to fit the page width
            new_table_col_width = (doc.pagesize[0] - 2 * 72) / 4  # Divide by the number of columns
            new_table = Table(process_mem_data, colWidths=[new_table_col_width] * 2)
            new_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONT', (0, 0), (-1, -1), 'font'),
                ('FONTNAME', (0, 0), (-1, -1), 'font'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                # ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid lines
                ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Increase bottom padding
            ]))

            # Add the new table to the elements list
            elements.append(new_table)

            elements.append(PageBreak())

##############################################################################################################################################

            # text_between_tables = Paragraph("사용 포트", process_style)
            # elements.append(text_between_tables)

            resource_data = [
                ['사용 포트']
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

            top_port_usages = get_unique_port_usage(selected_ip, start_date_obj, end_date_obj)

            # Define the new table data
            port_data = [
                ['Local', 'Peer', 'State', 'RecvQ', 'SendQ']
            ]

            for port_usage in top_port_usages:

                process_text = port_usage['process']

                if len(process_text) > 80:  
                    process_text = '...' + process_text[-77:]  
                
                port_data.append([process_text])

                local_text = port_usage['local']
                if len(local_text) > 20:  
                    local_text = '...' + local_text[-17:]  

                port_data.append([
                    local_text,
                    port_usage['peer'],
                    port_usage['state'],
                    port_usage['recvq'],
                    port_usage['sendq']
                ])

            # Adjust column widths to fit the page width
            new_table_col_width = (doc.pagesize[0] - 2 * 72) / 5 
            new_table = Table(port_data, colWidths=[new_table_col_width] * 2)
            new_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONT', (0, 0), (-1, -1), 'font'),
                ('FONTNAME', (0, 0), (-1, -1), 'font'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                # ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid lines
                ('TOPPADDING', (0, 0), (-1, -1), 6),  # Increase top padding
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Increase bottom padding
            ]))
            for i in range(1, len(port_data)):
                if i % 2 == 1:  
                    new_table.setStyle(TableStyle([
                        ('SPAN', (0, i), (-1, i)),  # 홀수행 병합
                    ]))
            
            elements.append(new_table)

            elements.append(PageBreak())


# ########################################################################################################################### 보고서


    # Build PDF
    doc.build(elements)

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    pdf = buffer.getvalue()
    buffer.close()

    response = FileResponse(io.BytesIO(pdf), as_attachment=True, filename='instance_report.pdf')
    return response