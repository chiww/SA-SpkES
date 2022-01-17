#!/usr/bin/env python
# coding=utf-8

from __future__ import absolute_import, division, print_function, unicode_literals
import traceback
from datetime import datetime
import json
import default
import time
from collections import OrderedDict
from splunklib.searchcommands import Configuration, Option, validators
from splunklib.searchcommands.search_command import SearchCommand
from splunklib.searchcommands.internals import MetadataEncoder
from splunklib.searchcommands.environment import splunklib_logger
from splunklib import six
from splunklib import data as spkdata
from elasticsearch import Elasticsearch, helpers

logger = splunklib_logger


class StringArrayValidator(validators.Validator):
    """ Validates field name option values as string of array .

    """

    def __call__(self, value):
        try:
            if value is None:
                return []
            else:
                return value.split(',')
        except Exception as e:
            raise ValueError('Invalid json: {0}  message:{1}'.format(six.text_type(value), traceback.format_exc()))

    def format(self, value):
        return [] if value is None else value.split(',')


class ESCommand(SearchCommand):
    """
    Elasticsearch base command class, but is not run in splunk, just for other command.
    """

    client = Option(
        doc='''
        **Syntax:** **client=***<client>*
        **Description:** Elasticsearch client configuration name.''',
        require=False)

    confile = Option(
        doc='''
            **Syntax:** **confile=***<str>*
            **Description:** which configure file want to select. default is <elasticsearch>.conf''',
        require=False, default='elasticsearch')

    # --------------------------------
    # helper.scan options
    # --------------------------------
    scroll = Option(
        doc='''
                **Syntax:** **scroll=***<str>*
                **Description:** Specify how long a consistent view of the index should be
        maintained for scrolled search''',
        require=False, default='5m')

    raise_on_error = Option(
        doc='''
                    **Syntax:** **raise_on_error=***<Bool>*
                    **Description:**raises an exception (``ScanError``) if an error is
        encountered (some shards fail to execute). By default we raise''',
        require=False, default=True)

    preserve_order = Option(
        doc='''
                    **Syntax:** **preserve_order=***<str>*
                    **Description:**don't set the ``search_type`` to ``scan`` - this will
        cause the scroll to paginate with preserving the order. Note that this
        can be an extremely expensive operation and can easily lead to
        unpredictable results, use with caution.''',
        require=False, default=False)

    size = Option(
        doc='''
                    **Syntax:** **size=***<int>*
                    **Description:**size (per shard) of the batch send at each iteration''',
        require=False, default=1000)

    request_timeout = Option(
        doc='''
                    **Syntax:** **request_timeout=***<str>*
                    **Description:** explicit timeout for each call to ``scan``''',
        require=False, default=None)

    clear_scroll = Option(
        doc='''
                    **Syntax:** **clear_scroll=***<Bool>*
                    **Description:**explicitly calls delete on the scroll id via the clear
        scroll API at the end of the method on completion or error, defaults
        to true.''',
        require=False, default=True)

    scroll_kwargs = Option(
        doc='''
                        **Syntax:** **scroll_kwargs=***<str>*
                        **Description:**additional kwargs to be passed to
        :meth:`~elasticsearch.Elasticsearch.scroll`''',
        require=False, default={})

    def get_command_options(self, names=None):
        if not names:
            names = self.command_options_names

        ops = dict()
        for ops_name, ops_obj in self.options.items():
            if ops_name not in names:
                continue
            if ops_obj.value is None:
                continue
            ops[ops_name] = ops_obj.value

        return ops

    @property
    def command_options_names(self):
        raise ImportError("Not rewrite command_options_names.")

    def prepare_output(self, data, conf):

        rowset = OrderedDict()
        rowset['source'] = conf.source
        rowset['sourcetype'] = conf.sourcetype

        if conf.timefield:
            timestamp = self.parser_timestamp(data.get(conf.timefield, None), conf.timeformat)
            if timestamp:
                rowset['_time'] = timestamp

        for key, value in data.items():
            if key in ['_time', 'host', 'sourcetype']:
                continue
            if isinstance(value, str):
                for separator in ['\r\n', '\n']:
                    if separator in value:
                        value = value.split(separator)
                        break
            rowset[key] = value
        rowset['_raw'] = json.dumps(data, ensure_ascii=False)
        return rowset

    @staticmethod
    def parser_timestamp(value, formatter):
        if isinstance(value, int):
            return value
        if not value or not formatter:
            return None
        return datetime.timestamp(datetime.strptime(value, formatter))

    def scan(self, conf, index="*", query=None):
        """

        :params: index
        :params: query
        :params:

        elasticsearch.helpers.scan(client, query=None, scroll='5m', raise_on_error=True, preserve_order=False, size=1000, request_timeout=None, clear_scroll=True, scroll_kwargs=None, **kwargs)¶

        Simple abstraction on top of the scroll() api - a simple iterator that yields all hits as returned by underlining scroll requests.

        By default scan does not return results in any pre-determined order. To have a standard order in the returned documents (either by score or explicit sort definition) when scrolling, use preserve_order=True. This may be an expensive operation and will negate the performance benefits of using scan.

        Parameters:
            client – instance of Elasticsearch to use
            query – body for the search() api
            scroll – Specify how long a consistent view of the index should be maintained for scrolled search
            raise_on_error – raises an exception (ScanError) if an error is encountered (some shards fail to execute). By default we raise.
            preserve_order – don’t set the search_type to scan - this will cause the scroll to paginate with preserving the order. Note that this can be an extremely expensive operation and can easily lead to unpredictable results, use with caution.
            size – size (per shard) of the batch send at each iteration.
            request_timeout – explicit timeout for each call to scan
            clear_scroll – explicitly calls delete on the scroll id via the clear scroll API at the end of the method on completion or error, defaults to true.
            scroll_kwargs – additional kwargs to be passed to scroll()
            Any additional keyword arguments will be passed to the initial search() call:

        scan(es,
            query={"query": {"match": {"title": "python"}}},
            index="orders-*",
            doc_type="books"
        )
        """

        def get_scan_options(cmd):
            ops = dict()
            scan_ops_fields = ['scroll', 'raise_on_error', 'preserve_order', 'size', 'request_timeout',
                               'clear_scroll', 'scroll_kwargs']
            for ops_name, ops_obj in cmd.options.items():
                if ops_name in scan_ops_fields:
                    ops[ops_name] = ops_obj.value
            return ops

        client_obj = Elasticsearch(**conf.client)
        for r in helpers.scan(client_obj, index=index, query=query, **get_scan_options(self)):
            yield r


class ESConf(object):

    def __init__(self, command):
        self.name = command.index
        self.command = command
        self._client_conf = {}
        self._index_conf = {}
        self.parse()

    @property
    def hosts(self):
        return self._client_conf['hosts']

    @property
    def user(self):
        return self._client_conf['user']

    @property
    def password(self):
        return self._client_conf['password']

    @property
    def timefield(self):
        return self._index_conf.get('timefield', None)

    @property
    def timeformat(self):
        return self._index_conf['timeformat']

    @property
    def source(self):
        return self._index_conf['source']

    @property
    def sourcetype(self):
        return self._index_conf['sourcetype']

    @property
    def client(self):
        return self._client_conf

    def index(self):
        return self._index_conf

    def get_configure(self, name):
        namespace = self.command.service.namespace
        path_segment = "properties/%s/%s" % (self.command.confile, name)
        response = self.command.service.get(path_segment, namespace.owner, namespace.app, namespace.sharing)
        body = response.body.read()
        feed = spkdata.load(body)
        entries = feed['feed'].get('entry', ())

        if isinstance(entries, spkdata.Record):
            entries = entries,

        settings = {entry['title']: entry['content'].get('$text', '') for entry in entries}
        return settings

    def parse(self):

        indexes = self.get_configure('index')['keys'].split(",")
        match = []
        for index in indexes:
            index = index.strip()
            if self.wildcard(self.name, index):
                match.append([index, len(index)])

        match.sort(key=lambda x: x[1], reverse=True)
        _index = match[0][0]
        self._index_conf = self.get_configure("index_" + _index)
        self._client_conf = self.get_configure("client_" + self._index_conf['client'])

        for key, value in self._client_conf.items():
            if key in ['hosts', 'http_auth']:
                self._client_conf[key] = value.split(',')
            if key == 'http_auth':
                self._client_conf[key] = tuple(self._client_conf[key])

    @staticmethod
    def wildcard(pre, cur):
        """
        :param  pre: the index from options which user input.
        :param cur: the index pattern from configure which user specified.
        """
        i, j, prestar, match = 0, 0, -1, -1
        while i < len(pre):
            if j < len(cur) and (pre[i] == cur[j] or cur[j] == "?"):
                i += 1
                j += 1
            elif j < len(cur) and cur[j] == "*":
                prestar = j
                j += 1
                match = i
            elif prestar != -1:
                j = prestar + 1
                i = match + 1
                match = i
            else:
                return False
        # 上一段代码只跟踪了字符串s，也就是pre，如果字符模式p字符串后面还有字符，如果后面的字符是*，那么可以继续看下一个字符
        while j < len(cur) and cur[j] == "*":
            j += 1
        # 如果当前位置不为字符串p的长度，说明做字符串p的*后面（如果有），还有未匹配的字符，说明两个字符串不完全匹配
        return j == len(cur)


class ESQueryStringQueryCommand(ESCommand):
    """
    Search some data from Elasticsearch by Query string query.
    https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html

    ##Syntax

    .. code-block::
        essearch domain=<domain> index=<ES_IndexName> query=<query>

    ##Example
    .. code-block ::
        | essearch index="jumper*" query="" ...
    """

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
        require=False, default="*")

    # (Optional, string) Default field you wish to search if no field is provided in the query string.
    #   Defaults to the index.query.default_field index setting, which has a default value of *.
    #   The * value extracts all fields that are eligible for term queries and filters the metadata fields.
    #   All extracted fields are then combined to build a query if no prefix is specified.
    #
    #   Searching across all eligible fields does not include nested documents. Use a nested query to search
    #   those documents.
    #
    #   For mappings with a large number of fields, searching across all eligible fields could be expensive.
    #
    #   There is a limit on the number of fields that can be queried at once. It is defined by the
    #   indices.query.bool.max_clause_count search setting, which defaults to 1024.
    default_field = Option(
        doc='''
            **Syntax:** **default_field=***<fieldname>*
            **Description:** query string body.''',
        require=False)

    # (Optional, Boolean) If true, the wildcard characters * and ? are allowed as the first character of the query
    # string. Defaults to true.
    allow_leading_wildcard = Option(
        doc='''
            **Syntax:** **allow_leading_wildcard=***<bool>*
            **Description:** query string body.''',
        require=False)

    # (Optional, Boolean) If true, the query attempts to analyze wildcard terms in the query string. Defaults to false.
    analyze_wildcard = Option(
        doc='''
            **Syntax:** **analyze_wildcard=***<bool>*
            **Description:** query string body.''',
        require=False)

    # (Optional, string) Analyzer used to convert text in the query string into tokens. Defaults to the index-time
    # analyzer mapped for the default_field. If no analyzer is mapped, the index’s default analyzer is used.
    analyzer = Option(
        doc='''
            **Syntax:** **analyzer=***<expression>*
            **Description:** query string body.''',
        require=False)

    # (Optional, Boolean) If true, match phrase queries are automatically created for multi-term synonyms.
    # Defaults to true. See Synonyms and the query_string query for an example.
    auto_generate_synonyms_phrase_query = Option(
        doc='''
            **Syntax:** **auto_generate_synonyms_phrase_query=***<bool>*
            **Description:** query string body.''',
        require=False)

    # (Optional, float) Floating point number used to decrease or increase the relevance scores of the query.
    # Defaults to 1.0.
    boost = Option(
        doc='''
            **Syntax:** **boost=***<float>*
            **Description:** query string body.''',
        require=False)

    # (Optional, string) Default boolean logic used to interpret text in the query string if no operators are
    # specified. Valid values are:
    #   OR (Default)
    #       For example, a query string of "capital of Hungary" is interpreted as "capital OR of OR Hungary".
    #   AND
    #       For example, a query string of "capital of Hungary" is interpreted as "capital AND of AND Hungary".
    default_operator = Option(
        doc='''
            **Syntax:** **default_operator=***<expression>*
            **Description:** query string body.''',
        require=False)

    # (Optional, Boolean) If true, enable position increments in queries constructed from a query_string search.
    # Defaults to true.
    enable_position_increments = Option(
        doc='''
            **Syntax:** **enable_position_increments=***<bool>*
            **Description:** query string body.''',
        require=False)

    # (Optional, array of strings) Array of fields you wish to search.
    fields = Option(
        doc='''
            **Syntax:** **fields=***<fieldname>*
            **Description:** 
                (Optional, array of strings) Array of fields you wish to search.
                You can use this parameter query to search across multiple fields. See Search multiple fields.''',
        require=False)

    # (Optional, string) Maximum edit distance allowed for fuzzy matching. For fuzzy syntax, see Fuzziness.
    fuzziness = Option(
        doc='''
            **Syntax:** **fuzziness=***<expression>*
            **Description:** query string body.''',
        require=False)

    # (Optional, integer) Maximum number of terms to which the query expands for fuzzy matching. Defaults to 50.
    fuzzy_max_expansions = Option(
        doc='''
            **Syntax:** **fuzzy_max_expansions=***<int>*
            **Description:** query string body.''',
        require=False)

    # (Optional, integer) Number of beginning characters left unchanged for fuzzy matching. Defaults to 0.
    fuzzy_prefix_length = Option(
        doc='''
            **Syntax:** **fuzzy_prefix_length=***<int>*
            **Description:** query string body.''',
        require=False)

    # (Optional, Boolean) If true, edits for fuzzy matching include transpositions of two adjacent characters (ab → ba).
    # Defaults to true.
    fuzzy_transpositions = Option(
        doc='''
            **Syntax:** **fuzzy_transpositions=***<bool>*
            **Description:** query string body.''',
        require=False)

    # (Optional, Boolean) If true, format-based errors, such as providing a text value for a numeric field, are ignored.
    # Defaults to false.
    lenient = Option(
        doc='''
            **Syntax:** **lenient=***<bool>*
            **Description:** query string body.''',
        require=False)

    # (Optional, integer) Maximum number of automaton states required for the query. Default is 10000.
    # Elasticsearch uses Apache Lucene internally to parse regular expressions. Lucene converts each regular expression
    # to a finite automaton containing a number of determinized states.
    #
    # You can use this parameter to prevent that conversion from unintentionally consuming too many resources. You may
    # need to increase this limit to run complex regular expressions.
    max_determinized_states = Option(
        doc='''
            **Syntax:** **max_determinized_states=***<int>*
            **Description:** query string body.''',
        require=False)

    # (Optional, string) Minimum number of clauses that must match for a document to be returned. See the
    # minimum_should_match parameter for valid values and more information. See How minimum_should_match works for
    # an example.
    minimum_should_match = Option(
        doc='''
            **Syntax:** **minimum_should_match=***<expression>*
            **Description:** query string body.''',
        require=False)

    # (Optional, string) Analyzer used to convert quoted text in the query string into tokens. Defaults to the
    # search_quote_analyzer mapped for the default_field.
    # For quoted text, this parameter overrides the analyzer specified in the "analyzer" parameter.
    quote_analyzer = Option(
        doc='''
            **Syntax:** **quote_analyzer=***<expression>*
            **Description:** query string body.''',
        require=False)

    # (Optional, integer) Maximum number of positions allowed between matching tokens for phrases. Defaults to 0. If 0,
    # exact phrase matches are required. Transposed terms have a slop of 2.
    phrase_slop = Option(
        doc='''
            **Syntax:** **phrase_slop=***<int>*
            **Description:** query string body.''',
        require=False)

    # (Optional, string) Suffix appended to quoted text in the query string.
    # You can use this suffix to use a different analysis method for exact matches. See Mixing exact search with
    # stemming.
    quote_field_suffix = Option(
        doc='''
            **Syntax:** **quote_field_suffix=***<expression>*
            **Description:** query string body.''',
        require=False)

    # (Optional, string) Method used to rewrite the query. For valid values and more information,
    # see the "rewrite" parameter.
    rewrite = Option(
        doc='''
            **Syntax:** **rewrite=***<expression>*
            **Description:** query string body.''',
        require=False)

    # (Optional, string) Coordinated Universal Time (UTC) offset or IANA time zone used to convert date values in the
    # query string to UTC.
    # Valid values are ISO 8601 UTC offsets, such as +01:00 or -08:00, and IANA time zone IDs,
    # such as America/Los_Angeles.
    time_zone = Option(
        doc='''
            **Syntax:** **time_zone=***<int>*
            **Description:** query string body.''',
        require=False)

    @property
    def command_options_names(self):
        return [
            'query', 'default_field', 'prefix', 'nested', 'allow_leading_wildcard', 'analyze_wildcard', 'analyzer',
            'auto_generate_synonyms_phrase_query', 'boost', 'default_operator', 'enable_position_increments', 'fields',
            'fuzziness', 'fuzzy_max_expansions', 'fuzzy_prefix_length', 'fuzzy_transpositions', 'lenient',
            'max_determinized_states', 'minimum_should_match', 'quote_analyzer', 'analyzer', 'phrase_slop',
            'quote_field_suffix', 'rewrite', 'time_zone']

    def get_query_string_query_options(self):
        return self.get_command_options()

    def query_dsl(self, conf, record=None):

        if record:
            # 重构填充query_string_query中query内容，实现填充上文的字段内容
            # ./howto/query_format_example.py
            if not self.fieldnames:
                _keys = list(set(record.keys()))
            else:
                _keys = list(set(record.keys()).intersection(set(self.fieldnames)))

            for key in _keys:
                if isinstance(record[key], list):
                    record[key] = "(%s)" % " OR ".join(record[key])
            self.query = self.query.format(**record)

        # 获取输入的参数
        ops = self.get_query_string_query_options()
        _must = [{'query_string': ops}]

        # 处理Elasticsearch中的时间区间
        metadata = json.loads(MetadataEncoder().encode(self.metadata))
        searchinfo = metadata['searchinfo']
        if not int(searchinfo['latest_time']):
            latest_time = datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%dT%H:%M:%S')
        else:
            latest_time = datetime.fromtimestamp(int(searchinfo['latest_time'])).strftime('%Y-%m-%dT%H:%M:%S')
        earliest_time = datetime.fromtimestamp(int(searchinfo['earliest_time'])).strftime('%Y-%m-%dT%H:%M:%S')

        if conf.timefield and conf.timefield not in ops['query']:
            _must.append({'range': {
                        conf.timefield: {
                            'gte': earliest_time,
                            'lte': latest_time
                        }
                    }})
        return {"query": {"bool": {"must": _must}}}

