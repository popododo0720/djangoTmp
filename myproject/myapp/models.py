from django.db import models

class CpuUsage(models.Model):
    timestamp = models.DateTimeField()
    cpu_usage = models.DecimalField(max_digits=4, decimal_places=1)
    ip_address = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'cpu_usage'

class MemUsage(models.Model):
    timestamp = models.DateTimeField()
    mem_usage = models.DecimalField(max_digits=4, decimal_places=1)
    ip_address = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'mem_usage'

class DiskUsage(models.Model):
    timestamp = models.DateTimeField()
    disk_size = models.IntegerField()
    disk_used = models.IntegerField()
    ip_address = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'disk_usage'

class InstanceProcessCpu(models.Model):
    command = models.TextField()
    pid = models.IntegerField()
    instance_user = models.TextField()
    instance = models.TextField()
    timestamp = models.DateTimeField()
    cpu_usage = models.DecimalField(max_digits=4, decimal_places=1)

    class Meta:
        managed = False 
        db_table = 'instance_process_cpu'

class InstanceProcessMem(models.Model):
    command = models.TextField()
    pid = models.IntegerField()
    instance_user = models.TextField()
    instance = models.TextField()
    timestamp = models.DateTimeField()
    mem_usage = models.DecimalField(max_digits=4, decimal_places=1)

    class Meta:
        managed = False 
        db_table = 'instance_process_mem'

class Instance(models.Model):
    id = models.IntegerField(primary_key=True)
    display_name = models.CharField(max_length=255)
    hostname = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    updated_at = models.DateTimeField()
    root_device_name = models.CharField(max_length=255)
    vcpus = models.IntegerField()
    memory_mb = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)  
    deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'instances'  

class BlockDeviceMapping(models.Model):
    id = models.IntegerField(primary_key=True)
    instance_uuid = models.CharField(max_length=36)

    class Meta:
        managed = False
        db_table = 'block_device_mapping'