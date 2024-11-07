# es.py
import json
from elasticsearch import Elasticsearch
from datetime import timedelta
from django.utils import timezone

ES_HOST = 'https://192.168.0.31:9200'  
ES_CA_CERT = '/home/con1/EFK/elasticsearch-8.15.1/config/certs/ca/ca.crt'    
ES_USER = 'elastic'                      
ES_PASSWORD = '-m1YLicBt+wa0t4ltxqq'               

ELASTICSEARCH_CLIENT = Elasticsearch(
    [ES_HOST],
    http_auth=(ES_USER, ES_PASSWORD),
    verify_certs=True,
    ca_certs=ES_CA_CERT,
)

def generate_date_range(start_date_obj, end_date_obj):
    current_date = start_date_obj.date()
    end_date = end_date_obj.date()
    
    date_range = []
    while current_date <= end_date:
        date_range.append(current_date)
        current_date += timedelta(days=1)
    
    return date_range

def fetch_log_levels_for_date_range(selected_ip, start_date_obj, end_date_obj):
    date_range = generate_date_range(start_date_obj, end_date_obj)
    ip_suffix = selected_ip.split(':')[0].split('.')[-1]
    
    all_buckets = []
    
    for date in date_range:
        today_date = date.strftime("%Y.%m.%d")  
        index_pattern = f"{ip_suffix}syslog_logs_{today_date}*"
        
        buckets = fetch_log_levels(index_pattern)
        all_buckets.extend(buckets) 

    log_levels = filter_log_levels(all_buckets)
    return log_levels

def fetch_log_levels(index_pattern):
    try:
        response = ELASTICSEARCH_CLIENT.search(
            index=index_pattern, 
            body={
                "size": 0,
                "aggs": {
                    "log_levels": {
                        "terms": {
                            "field": "log_level.keyword",
                            "size": 10
                        }
                    }
                }
            }
        )
        return response['aggregations']['log_levels']['buckets']
    except Exception as e:
        print(f"Error fetching log levels for index pattern '{index_pattern}': {e}")
        return []

def filter_log_levels(buckets):
    log_levels = {
        'INFO': 0,
        'WARN': 0,
        'ERROR': 0,
        'FATAL': 0
    }

    for bucket in buckets:
        log_levels[bucket['key']] += bucket['doc_count']

    result = [{'level': level, 'count': count} for level, count in log_levels.items()]
    return result
