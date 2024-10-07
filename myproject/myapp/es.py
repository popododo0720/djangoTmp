# es.py
import json
from elasticsearch import Elasticsearch

# Elasticsearch 설정
ES_HOST = 'https://192.168.0.42:9200'  # Elasticsearch 서버 주소
ES_CA_CERT = '/home/coremax/EFK/elasticsearch-8.15.1/config/certs/ca/ca.crt'     # CA 인증서 경로
ES_USER = 'elastic'                      # Elasticsearch 사용자
ES_PASSWORD = 'asdfasdf'                  # Elasticsearch 비밀번호

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
    # 'ERROR'와 'ERR'를 합쳐서 'ERROR'로 처리
    error_count = 0
    desired_levels = ['INFO', 'WARNING', 'DBG']  # 'ERR'는 제외

    result = []

    for bucket in buckets:
        if bucket['key'] == 'ERR':
            error_count += bucket['doc_count']  # 'ERR' 로그 수를 더합니다.
        elif bucket['key'] == 'ERROR':
            error_count += bucket['doc_count']  # 'ERROR' 로그 수를 더합니다.
        elif bucket['key'] in desired_levels:
            result.append({'level': bucket['key'], 'count': bucket['doc_count']})

    # 'ERROR' 레벨을 추가합니다. (합산한 값)
    if error_count > 0:
        result.append({'level': 'ERROR', 'count': error_count})

    return result
