# es.py
import json
from elasticsearch import Elasticsearch

# Elasticsearch 설정
ES_HOST = 'https://192.168.0.31:9200'  # Elasticsearch 서버 주소
ES_CA_CERT = '/home/con1/EFK/elasticsearch-8.15.1/config/certs/ca/ca.crt'     # CA 인증서 경로
ES_USER = 'elastic'                      # Elasticsearch 사용자
ES_PASSWORD = '-m1YLicBt+wa0t4ltxqq'                  # Elasticsearch 비밀번호

# Elasticsearch 클라이언트 초기화
ELASTICSEARCH_CLIENT = Elasticsearch(
    [ES_HOST],
    http_auth=(ES_USER, ES_PASSWORD),
    verify_certs=True,
    ca_certs=ES_CA_CERT,
)

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
        print(f"Error fetching log levels: {e}")
        return []

def filter_log_levels(buckets):
    log_levels = {
        'INFO': 0,
        'WARN': 0,
        'FATAL': 0,
        'ERROR': 0  
    }

    for bucket in buckets:
        log_levels[bucket['key']] += bucket['doc_count']

    result = [{'level': level, 'count': count} for level, count in log_levels.items()]

    return result
