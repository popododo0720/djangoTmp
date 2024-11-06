from myapp.service import *
from .es import *
from django.utils import timezone
from django.db import connections
from django.utils.timezone import make_aware
from django.urls import reverse
from django.http import JsonResponse
from .tem_basic import *
from .tem_logmaster import *
    
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
            i.uuid
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

        ip_mapping_query = get_report_ip_mapping(row[9])
        ip_addresses = []
        report_type = ""

        for entry in ip_mapping_query:
            if entry.get('ip_address'):
                ip_addresses.extend(entry['ip_address']) 
            if entry.get('report_type'):
                report_type = entry['report_type'] 

        ip_addresses_str = ', '.join(ip_addresses) if ip_addresses else ""
        report_type = report_type or "default"

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
            'report_type': report_type,
        })

    return JsonResponse({'data': data})

def report_view(request, instanceUuid):

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    query = '''
            SELECT 
            i.id
        FROM 
            instances i 
        WHERE
            i.vm_state = 'active' AND i.uuid = %s;
            '''

    with connections['mariadb_nova'].cursor() as cursor:
        cursor.execute(query, [instanceUuid])
        rows = cursor.fetchall()

    instanceId = rows[0][0]
    ip_mapping_query = get_report_ip_mapping(instanceUuid)
    ip_addresses = []
    reportType = "default"

    for entry in ip_mapping_query:
        if entry.get('ip_address'):
            ip_addresses.extend(entry['ip_address']) 
        if entry.get('report_type'):
            reportType = entry['report_type']

    if not ip_addresses:
        ip_addresses = ['']
            
    match reportType:
        case 'logmaster':
            response = logmaster_view(request, instanceId, start_date, end_date)
        case _:
            response = basic_view(request, instanceId, start_date, end_date)
        
    print(instanceId)
    print(reportType)
    print(ip_mapping_query)
    print(start_date + " " + end_date)
    return response