from myapp.service import *
from .es import *
from django.utils import timezone
from django.db import connections
from django.utils.timezone import make_aware
from django.urls import reverse
from django.http import JsonResponse
from .tem_basic import *
from .tem_other import *
from .tem_test import *
from django.http import HttpResponse
import requests
    
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

    prometheus_url = 'http://10.0.2.110:9091/api/v1/targets'
    auth = ('admin', 'JOBdRRi8IvBPnmSdxZ1V7tum15VfaJcVkQ5zigZ6')

    try:
        response = requests.get(prometheus_url, auth=auth)
        response.raise_for_status()  
        targets_data = response.json()  
        
        targets = targets_data.get('data', {}).get('activeTargets', [])

        prometheus_targets = []
        for target in targets:
            job = target.get('labels', {}).get('job', '')
            if job == 'custom_exporter' and target.get('health', 'N/A') == 'up':  
                instance = target.get('labels', {}).get('instance')
                ip_address = instance.split(':')[0] if instance else ''
                if ip_address:
                    prometheus_targets.append(ip_address)
    except requests.RequestException as e:
        prometheus_targets = {'error': str(e)}
    
    data = []
    for row in rows:
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

        if not any(ip in prometheus_targets for ip in ip_addresses):
            continue
 
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
            'device': row[6],
            'vcpus': row[7],
            'memory_mb': row[8],
            'instance_uuid': row[9],
            'image': "ubuntu",
            'ip_addresses': ip_addresses_str,
            'report_type': report_type,
        })

    return JsonResponse({'data': data})

###########################################################################################

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
    
    # response = test_view(request, instanceId, reportType, start_date, end_date)

    if(reportType=='default'):
        response = basic_view(request, instanceId, start_date, end_date)
    else:
        response = template_view(request, instanceId, reportType, start_date, end_date)
        
    return response