#!/usr/bin/env python
# coding=utf-8


from __future__ import absolute_import, division, print_function, unicode_literals
import traceback
import ipaddress
import json
from datetime import datetime

from splunklib.searchcommands import validators
from splunklib import six
from spkmodifiers import Modifiers


class JsonValidator(validators.Validator):
    """ Validates field name option values as json.

    """

    def __call__(self, value):
        try:
            if value is None:
                return dict()
            else:
                return json.loads(value.replace("'", "\""))
        except Exception as e:
            raise ValueError('Invalid json: {0}  message:{1}'.format(six.text_type(value), traceback.format_exc()))

    def format(self, value):
        return None if value is None else six.text_type(value)


class IPValidator(validators.Validator):
    """ Validates field name option values as json.

    """

    def __call__(self, value):
        try:
            if value is None:
                return ''
            else:
                ipaddress.ip_address(six.text_type(value))
                return six.text_type(value)
        except Exception as e:
            raise ValueError('Invalid IP address: {0}  message:{1}'.format(six.text_type(value), traceback.format_exc()))

    def format(self, value):
        return '' if value is None else six.text_type(value)


class TimeRangeValidator(validators.Validator):
    """ Validates field name option values as '-d@m'.

    """

    TIME_PARTITION_CHARACTER = '#'
    DEFAULT_TIME_FIELD = 'createTime'
    DEFAULT_QUERY_START = '%s>:start' % DEFAULT_TIME_FIELD
    DEFAULT_QUERY_END = '%s<:end' % DEFAULT_TIME_FIELD

    def __call__(self, value):

        if not value:
            return self.TIME_PARTITION_CHARACTER

        try:
            valid, message = self.expression_validator(value)
            if not valid:
                raise ValueError('Invalid format, %s' % message)
            else:
                return six.text_type(value)
        except Exception as e:
            raise ValueError('Invalid format {0}, but: {1}.'.format(str(e), six.text_type(value)))

    def format(self, value):
        return '' if value is None else six.text_type(value)

    @staticmethod
    def _is_timestamp(value):
        try:
            int(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_modifiers(value):
        if not value:
            return True
        m = Modifiers(value)
        return m.validation()

    @staticmethod
    def _is_datetime(value):
        try:
            datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return True
        except Exception:
            return False

    def expression_validator(self, value):

        if self.TIME_PARTITION_CHARACTER not in value or len(value.split(self.TIME_PARTITION_CHARACTER)) != 2:
            return False, 'Time range must contains only one [%s], input is  [%s]' % (self.TIME_PARTITION_CHARACTER, value)
        _st_expression, _ed_expression = value.split(self.TIME_PARTITION_CHARACTER)
        for expression in [_st_expression.strip(), _ed_expression.strip()]:
            if self._is_timestamp(expression) or self._is_modifiers(expression) or self._is_datetime(expression):
                continue
            else:
                return False, 'Time range must one of [ 1630660555<timestamp> | ' \
                              '-d@h<modifiers> | 2021-08-31 23:00:00 <datetime> ] but input: [%s]' % expression
        return True, ''

    def parse(self, expression):
        mdf = {
            'format': None,
            'value': ''
        }

        if not expression:
            return mdf

        if self._is_timestamp(expression):
            mdf['format'] = 'timestamp'
            mdf['value'] = int(expression)

        if self._is_modifiers(expression):
            mdf['format'] = 'modifier'
            mdf['value'] = six.text_type(expression)

        if self._is_datetime(expression):
            mdf['format'] = 'datetime'
            mdf['value'] = six.text_type(expression)

        return mdf


class ListByStrValidator(validators.Validator):
    """ Validates field name option values as json.

    """

    def __call__(self, value):
        try:
            if value is None:
                return six.text_type('')
            else:
                value.split(',')
                return six.text_type(value)
        except Exception as e:
            raise ValueError('Invalid json: {0}  message:{1}'.format(six.text_type(value), traceback.format_exc()))

    def format(self, value):
        return six.text_type('') if value is None else six.text_type(value)