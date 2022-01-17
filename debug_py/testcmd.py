import sys, json
import default
import splunk.Intersplunk as spi
import requests
from elasticsearch import Elasticsearch, helpers

# spi.parseError("[+] {}".format(str(settings)))


def output_result():
    results, dummyresults, settings = spi.getOrganizedResults()
    for result in results:
        spi.outputResults([result])


def es_scan():

    client = Elasticsearch(['127.0.0.1:9200'])
    for raw in helpers.scan(client, index='logstash-2015.05.20', query={'query': {'query_string': {'query': '*'}}}):
        try:
            data = dict()
            for k, v in raw['_source'].items():
                data[str(k)] = str(v)
            spi.outputStreamResults(data)
        except Exception as e:
            spi.parseError("[+] {}".format(str(e)))
            pass

# spi.outputResults(r)


if __name__ == '__main__':
    # output_result()
    es_scan()



