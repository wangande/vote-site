#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import setting
import inspect
from tornado.options import options


__all__ = ["BaseService", "BaseErrorException"]


class FieldException(object):
    def __init__(self, arg):
        self.arg = arg


class BaseErrorCodeDefine(object):
    """错误码定义"""
    REQ_PARAM_ERROR = 0x0001
    SERVER_ERROR = 0x0002


# 错误码对应的错误信息
Base_Error_Code_MAP = {
    BaseErrorCodeDefine.REQ_PARAM_ERROR: "Request Param Error",
    BaseErrorCodeDefine.SERVER_ERROR: "Server Error",
}


class BaseErrorException(Exception):
    """错误Exception"""

    def __init__(self, error_code):
        self.error_code = error_code
        try:
            current_call = inspect.stack()[1]
            _iframe = current_call[0]
            self.line_no = _iframe.f_lineno
            self.module_name = _iframe.f_globals.get("__name__", "")
            self.method_name = current_call[3]
            self.class_name = _iframe.f_locals.get('self', None).__class__.__name__

        except (IndexError, AttributeError):
            self.line_no = ''
            self.module_name = ''
            self.method_name = ''
            self.class_name = ''

    def __repr__(self):
        msg = Base_Error_Code_MAP.get(self.error_code, '')
        return "[*] Error:%s > %s. module: %s, class: %s, method: %s, line: %s " % (self.error_code, msg,
                                                                                    self.module_name,
                                                                                    self.class_name,
                                                                                    self.method_name,
                                                                                    self.line_no)

    def __str__(self):
        return Base_Error_Code_MAP.get(self.error_code, 'not find any match msg for code:%s' % self.error_code)


class BaseService(dict):
    def __init__(self):
        self.ch = options.get('ch')
        # self.fastdfs_client = options.get('fastdfs_client', None)
        self.redis_client = options.get('redis_client')

    def init(self):
        pass

    def parse_page(self, page, page_size):
        query = {}
        page = page or 1
        page_size = page_size or setting.PAGE_SIZE
        pos = (int(page) - 1) * int(page_size)

        query['pos'] = pos
        query['count'] = page_size
        return query

    def _(self, text):
        """ Localisation shortcut """
        return self.locale.translate(text).encode("utf-8")

    def get_fields(self, model_cls):
        fields = {}
        for f in model_cls.__dict__:
            if type(model_cls.__dict__[f]) == bool:
                fields[f] = model_cls.__dict__[f]
        return fields


