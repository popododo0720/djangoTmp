from datetime import datetime
from django.utils import timezone
from django.db.models import Avg
from .models import *
from datetime import timedelta

def get_resource_usage_averages(instance_ip, start_date, end_date):
    # CPU 사용량 평균 
    cpu_data = CpuUsage.objects.filter(
        timestamp__range=(start_date, end_date),
        ip_address=instance_ip
    ).aggregate(avg_cpu_usage=Avg('cpu_usage'))

    # 메모리 사용량 평균 
    mem_data = MemUsage.objects.filter(
        timestamp__range=(start_date, end_date),
        ip_address=instance_ip
    ).aggregate(avg_mem_usage=Avg('mem_usage'))

    # 디스크 크기 평균 
    disk_size_data = DiskUsage.objects.filter(
        timestamp__range=(start_date, end_date),
        ip_address=instance_ip
    ).aggregate(avg_disk_size=Avg('disk_size'))

    # 디스크 사용량 평균 
    disk_used_data = DiskUsage.objects.filter(
        timestamp__range=(start_date, end_date),
        ip_address=instance_ip
    ).aggregate(avg_disk_used=Avg('disk_used'))

    avg_cpu_usage_value = cpu_data['avg_cpu_usage']
    avg_mem_usage_value = mem_data['avg_mem_usage']
    avg_disk_size_value = int(disk_size_data['avg_disk_size']) if disk_size_data['avg_disk_size'] is not None else 0
    avg_disk_used_value = int(disk_used_data['avg_disk_used']) if disk_used_data['avg_disk_used'] is not None else 0

    return avg_cpu_usage_value, avg_mem_usage_value, avg_disk_size_value, avg_disk_used_value

def get_process_cpu_usage_top5(instance_ip, start_date, end_date):
    top_cpu_usages = InstanceProcessCpu.objects.filter(
        instance=instance_ip,
        timestamp__range=(start_date, end_date)
    ).values(
        'command', 'pid', 'instance_user'
    ).annotate(
        avg_cpu_usage=Avg('cpu_usage')
    ).order_by(
        '-avg_cpu_usage'
    )[:5]

    return top_cpu_usages

def get_process_mem_usage_top5(instance_ip, start_date, end_date):
    top_mem_usages = InstanceProcessMem.objects.filter(
        instance=instance_ip,
        timestamp__range=(start_date, end_date)
    ).values(
        'command', 'pid', 'instance_user'
    ).annotate(
        avg_mem_usage=Avg('mem_usage')
    ).order_by(
        '-avg_mem_usage'
    )[:5]

    return top_mem_usages


def get_unique_port_usage(instance_ip, start_date, end_date):
    unique_port_usages = (
        InstancePortMem.objects.filter(
            instance=instance_ip,
            timestamp__range=(start_date, end_date)
        )
        .values('state', 'recvq', 'sendq', 'local', 'peer', 'process') 
        .distinct() 
    )

    return unique_port_usages

def get_report_ip_mapping(instanceUuid):
    reportMapping = (
        ReportMapping.objects.filter(
            instance_uuid=instanceUuid,
        )
        .values('ip_address','report_type') 
        .distinct() 
    )

    return reportMapping

def get_report_type(reportType):
    reportTypeMapping = (
        ReportTypes.objects.filter(
            report_type=reportType,
        )
        .values('engine_name', 'engine_info')
        .distinct()
    )
    return reportTypeMapping

def get_count_for_command(command, instance, start_date, end_date):
    count = InstanceProcessCpu.objects.filter(
        command=command,
        instance=instance,
        timestamp__range=(start_date, end_date)
    ).count()

    closest_entry = InstanceProcessCpu.objects.filter(
        command=command,
        instance=instance,
        timestamp__range=(start_date, end_date)
    ).order_by('timestamp').last()

    if closest_entry.timestamp.tzinfo is None:
        closest_entry.timestamp = timezone.make_aware(closest_entry.timestamp, timezone.get_current_timezone())
    
    time_difference = abs(closest_entry.timestamp - end_date)
    is_within_5_minutes = time_difference <= timedelta(minutes=5)
    
    return count, is_within_5_minutes