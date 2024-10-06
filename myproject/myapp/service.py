from datetime import datetime
from django.utils import timezone
from django.db.models import Avg
from .models import *

def get_resource_usage_averages(instance_ip):
    # 계산할 시작일과 종료일 설정
    start_date = timezone.make_aware(datetime(2024, 9, 1, 0, 0, 0))
    end_date = timezone.make_aware(datetime(2024, 10, 30, 23, 59, 59))

    # CPU 사용량 평균 계산
    cpu_data = CpuUsage.objects.filter(
        timestamp__range=(start_date, end_date),
        ip_address=instance_ip
    ).aggregate(avg_cpu_usage=Avg('cpu_usage'))

    # 메모리 사용량 평균 계산
    mem_data = MemUsage.objects.filter(
        timestamp__range=(start_date, end_date),
        ip_address=instance_ip
    ).aggregate(avg_mem_usage=Avg('mem_usage'))

    # 디스크 크기 평균 계산
    disk_size_data = DiskUsage.objects.filter(
        timestamp__range=(start_date, end_date),
        ip_address=instance_ip
    ).aggregate(avg_disk_size=Avg('disk_size'))

    # 디스크 사용량 평균 계산
    disk_used_data = DiskUsage.objects.filter(
        timestamp__range=(start_date, end_date),
        ip_address=instance_ip
    ).aggregate(avg_disk_used=Avg('disk_used'))

   # 평균값 반환
    avg_cpu_usage_value = cpu_data['avg_cpu_usage']
    avg_mem_usage_value = mem_data['avg_mem_usage']
    avg_disk_size_value = int(disk_size_data['avg_disk_size']) if disk_size_data['avg_disk_size'] is not None else 0
    avg_disk_used_value = int(disk_used_data['avg_disk_used']) if disk_used_data['avg_disk_used'] is not None else 0

    return avg_cpu_usage_value, avg_mem_usage_value, avg_disk_size_value, avg_disk_used_value

def get_process_cpu_usage_top5(instance_ip):
    # 계산할 시작일과 종료일 설정
    start_date = timezone.make_aware(datetime(2024, 9, 1, 0, 0, 0))
    end_date = timezone.make_aware(datetime(2024, 9, 30, 23, 59, 59))

    # CPU 사용량 top5
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

def get_process_mem_usage_top5(instance_ip):
    # 계산할 시작일과 종료일 설정
    start_date = timezone.make_aware(datetime(2024, 9, 1, 0, 0, 0))
    end_date = timezone.make_aware(datetime(2024, 9, 30, 23, 59, 59))

    # CPU 사용량 top5
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