#!/usr/bin/env python
# coding=utf-8

from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import default
import traceback
from splunklib.searchcommands import dispatch, StreamingCommand, Configuration, Option, validators
from escommand import ESQueryStringQueryCommand, ESConf


@Configuration()
class EsLookupCommand(ESQueryStringQueryCommand, StreamingCommand):
    """
    """

    def stream(self, records):
        """

        #  multi value:
            | makeresults
            | eval q="POINS"
            | append
                [ makeresults
                | eval q="FALSTAFF" ]
            | stats values(q) as q
            | eslookup index=shakesp* query="speaker:{q}"

        # single value:
            | makeresults
            | eval q="POINS"
            | eslookup index=shakesp* query="speaker:{q}"

        """

        try:
            conf = ESConf(self)
        except KeyError as e:
            self.error_exit(e, "Can not get configure[%s] from configure file, please check %s.conf" % self.confile)
            return

        try:
            for record in records:
                for r in self.scan(conf, index=self.index, query=self.query_dsl(conf, record=record)):
                    yield self.prepare_output(r['_source'], conf)
        except Exception as error:
            self.error_exit(error, "Run error: \n%s" % str(traceback.format_exc()))

        return


dispatch(EsLookupCommand, sys.argv, sys.stdin, sys.stdout, __name__)

