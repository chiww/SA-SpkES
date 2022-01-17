#!/usr/bin/env python
# coding=utf-8

from __future__ import absolute_import, division, print_function, unicode_literals
import default
import sys
from splunklib.searchcommands import dispatch, EventingCommand, Configuration, Option, validators
from splunklib import data


@Configuration()
class ESDebugEVCommand(EventingCommand):
    """ Search some data from Elasticsearch by Query string query.
    https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html

    ##Syntax

    .. code-block::
        essearch index=<ES_IndexName> query=<query>

    ##Example
    .. code-block ::
        | essearch index="jumper*" query="" ...
    """
    domain = Option(
        doc='''
        **Syntax:** **index=***<ES_IndexName>*
        **Description:** Elasticsearch Index name.''',
        require=True, default='default')

    index = Option(
        doc='''
        **Syntax:** **index=***<ES_IndexName>*
        **Description:** Elasticsearch Index name.''',
        require=True)

    # (Required, string) Query string you wish to parse and use for search
    query = Option(
        doc='''
            **Syntax:** **query=***<query>*
            **Description:** query string body.''',
        require=True)

    def transform(self, records):

        data = dict()
        data['options'] = str(self.options)
        data['namespace'] = str(self.service.namespace)
        data['service_confs'] = self.service.confs['elasticsearch']
        data['configure'] = self.get_configure(domain=self.domain)
        data['hosts'] = self.get_configure(domain=self.domain)['hosts'].split(',')
        data['query'] = self.query

        data['records'] = str([r['q'] for r in records])
        yield data

    def get_configure(self, domain="default"):
        namespace = self.service.namespace
        path_segment = "properties/elasticsearch/" + domain
        response = self.service.get(path_segment, namespace.owner, namespace.app, namespace.sharing)
        body = response.body.read()
        feed = data.load(body)
        entries = feed['feed'].get('entry', ())

        if isinstance(entries, data.Record):
            entries = entries,

        settings = {entry['title']: entry['content'].get('$text', '') for entry in entries}
        return settings



dispatch(ESDebugEVCommand, sys.argv, sys.stdin, sys.stdout, __name__)


