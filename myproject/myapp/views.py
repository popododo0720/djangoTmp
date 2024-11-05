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
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
from django.db import connections
from datetime import datetime
from django.utils.timezone import make_aware
from django.urls import reverse
from django.http import JsonResponse

    
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
            i.id = b.id
        WHERE
            i.vm_state = 'active';
    '''

    with connections['mariadb_nova'].cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

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

        ip_mapping = get_report_ip_mapping(row[1])

        if not ip_mapping.exists():  
            ip_addresses_str = "" 
        else:
            ip_addresses = ip_mapping.values_list('ip_address', flat=True)
            ip_addresses_str = ', '.join(ip_addresses[0]) if ip_addresses else ""

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

    return JsonResponse({'data': data})


        