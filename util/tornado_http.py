#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import tornado.gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")

"""
Tornado Http 封装，支持异步http请求
"""


class TornadoHttp(object):
    """Tornado http"""
    def __init__(self, http_proxy=None):
        """初始化，http代理服务"""

        init_http_proxy = {}
        if http_proxy:
            init_http_proxy = http_proxy

        self.proxy_host = init_http_proxy.get("proxy_host", None)
        self.proxy_port = init_http_proxy.get("proxy_port", None)
        self.proxy_username = init_http_proxy.get("proxy_username", None)
        self.proxy_password = init_http_proxy.get("proxy_password", None)

    @tornado.gen.engine
    def get(self, url, data="", headers=None, timeout=60, callback=None):
        """
        tornado http get 请求
        :param url: 请求地址
        :param data: 请求查询参数
        :param headers: http头部
        :param timeout: 超时时间
        :param callback:
        :return:
        """

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest('%s?%s' % (url, urllib.urlencode(data)), headers=headers,
                                   proxy_host=self.proxy_host, proxy_port=self.proxy_port,
                                   proxy_username=self.proxy_username, proxy_password=self.proxy_password,
                                   request_timeout=timeout)

        response = yield tornado.gen.Task(http_client.fetch, http_request)
        callback(response)

    @tornado.gen.engine
    def post(self, url, data=None, headers=None, timeout=60, callback=None):
        """
        tornado http post 请求
        :param url: 请求地址
        :param data: 请求数据
        :param headers: 请求查询参数
        :param timeout: http头部
        :param callback:
        :return:
        """

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(url, method="POST", headers=headers, body=data,
                                   proxy_host=self.proxy_host, proxy_port=self.proxy_port,
                                   proxy_username=self.proxy_username, proxy_password=self.proxy_password,
                                   request_timeout=timeout)

        response = yield tornado.gen.Task(http_client.fetch, http_request)
        callback(response)

    @tornado.gen.engine
    def put(self, url, data=None, headers=None, timeout=60, callback=None):
        """
        tornado http put 请求
        :param url: 请求地址
        :param data: 请求查询参数
        :param headers: http头部
        :param timeout: 超时时间
        :param callback:
        :return:
        """

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(url, method="PUT", headers=headers, body=data,
                                   proxy_host=self.proxy_host, proxy_port=self.proxy_port,
                                   proxy_username=self.proxy_username, proxy_password=self.proxy_password,
                                   request_timeout=timeout)

        response = yield tornado.gen.Task(http_client.fetch, http_request)
        callback(response)

    @tornado.gen.engine
    def delete(self, url, data="", headers=None, timeout=60, callback=None):
        """
        tornado http delete 请求
        :param url: 请求地址
        :param data: 请求查询参数
        :param headers: http头部
        :param timeout: 超时时间
        :param callback:
        :return:
        """

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest('%s?%s' % (url, urllib.urlencode(data)), method="DELETE", headers=headers,
                                   proxy_host=self.proxy_host, proxy_port=self.proxy_port,
                                   proxy_username=self.proxy_username, proxy_password=self.proxy_password,
                                   request_timeout=timeout)

        response = yield tornado.gen.Task(http_client.fetch, http_request)
        callback(response)
