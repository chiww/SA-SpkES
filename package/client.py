import pprint
from elasticsearch import Elasticsearch, helpers

# curl -XGET -H "Authorization: Basic ZWxhc3RpYzpwYXNzd29yZA==" http://127.0.0.1:9200
es = Elasticsearch(['127.0.0.1:9200'],
                   http_auth=('elastic', 'elastic'),
                   scheme="http")


def __search():
    res = es.search(index="bank", body={"query": {"match_all": {}}})
    print("Got %d Hits:" % res['hits']['total']['value'])
    n = 0
    for hit in res['hits']['hits']:
        n += 1
    print(n)

def __search2():
    res = es.search(index="logstash-*", body={
        "query": {
            'bool': {
                'must': [
                    {'query_string': {'query': '*'}},
                    {'range': {
                        '@timestamp': {
                            'gte': '2015-05-19T04:29:38',
                            'lte': '2015-05-19T05:00:38'
                        }
                    }}
                ]
            },
        }})
    print("Got %d Hits:" % res['hits']['total']['value'])
    n = 0
    for hit in res['hits']['hits']:
        n += 1
    print(n)

import pprint
from datetime import datetime

def __scan():
    # res = helpers.scan(es, index="bank", query={"query": {"match_all": {}}})
    # res = helpers.scan(es, index="logstash-2015.05.20", query={'query': {'query_string': {'query': '*'}}})
    res = helpers.scan(es, index="logstash-*", query={
        "query": {
            'bool': {
                'must': [
                    {'query_string': {'query': '*'}},
                    {'range': {
                        '@timestamp': {
                            'gte': '2015-05-19T04:29:38',
                            'lte': '2015-05-19T05:00:38'
                        }
                    }}
                ]
            },
        }})
    n = 0
    for r in res:
        pprint.pprint(r['_source']['@timestamp'])
        print(datetime.strptime(r['_source']['@timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ'))
        n += 1
    print(n)


if __name__ == '__main__':
    #__search()
    __scan()
