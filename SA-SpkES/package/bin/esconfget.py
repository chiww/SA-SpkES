#!/usr/bin/env python
# coding=utf-8

from __future__ import absolute_import, division, print_function, unicode_literals
import default
import sys
from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration
from escommand import ESCommand


@Configuration()
class ESConfGetCommand(ESCommand, GeneratingCommand):
    """ Return elasticsearch configure file settings from conf file..

    ##Syntax

    .. code-block::
        | esconfget domain=<domain> confile=<confile>

    ##Example
    .. code-block ::
        | essearch domain="default"  ...
    """

    def generate(self):
        data = dict()
        data['options'] = str(self.options)
        data['namespace'] = str(self.service.namespace)
        data['service_confs'] = [{'domain': item.name, 'settings': item.content} for item in
                                 self.service.confs[str(self.confile)].iter()]
        data['domain_configure'] = self.get_configure(domain=self.domain)
        yield data


dispatch(ESConfGetCommand, sys.argv, sys.stdin, sys.stdout, __name__)

