#!/usr/bin/env python
# coding=utf-8

from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import traceback
import default

from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration
from escommand import ESQueryStringQueryCommand, ESConf


@Configuration(streaming=True)
class EsSearchCommand(ESQueryStringQueryCommand, GeneratingCommand):
    """ Search some data from Elasticsearch by Query string query.
    https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html

    ##Syntax

    .. code-block::
        essearch domain=<domain> index=<ES_IndexName> query=<query>

    ##Example
    .. code-block ::
        | essearch domain=default index="logstash-2015*" query=*
    """

    def generate(self):

        # | essearch domain=jumpserver index=security_jumpserver*
        # query="user:*01390586* AND @timestamp:[2021-11-08 TO 2021-11-09]"

        try:
            conf = ESConf(self)
        except KeyError as e:
            self.error_exit(e, "Can not get configure[%s] from configure file, please check %s.conf" % self.confile)
            return

        try:
            for r in self.scan(conf, index=self.index, query=self.query_dsl(conf)):
                yield self.prepare_output(r['_source'], conf)
        except Exception as error:
            self.error_exit(error, "Run error: \n%s" % str(traceback.format_exc()))

        return


dispatch(EsSearchCommand, sys.argv, sys.stdin, sys.stdout, __name__)

