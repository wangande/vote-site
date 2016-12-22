#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import simplejson
import tornado.web
import tornado.gen

from views.base import RequestHandler
from util import ip


class ApiHandler(RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self, *args, **kwargs):
        if not hasattr(self, '_get_'):
            raise tornado.web.HTTPError(405)

        self._get_(*args, **kwargs)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self, *args, **kwargs):
        if not hasattr(self, '_post_'):
            raise tornado.web.HTTPError(405)

        self._post_(*args, **kwargs)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def put(self, *args, **kwargs):
        if not hasattr(self, '_put_'):
            raise tornado.web.HTTPError(405)

        self._put_(*args, **kwargs)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def delete(self, *args, **kwargs):
        if not hasattr(self, '_delete_'):
            raise tornado.web.HTTPError(405)

        self._delete_(*args, **kwargs)

    @property
    def mail_connection(self):
        return self.application.mail_connection

    def render_success(self, result):
        self.set_header("Content-Type", 'application/json')
        self.write(simplejson.dumps(result))
        self.finish()

    def render_error(self, msg='', status=400, code=400):
        error = {
            'status': 'error',
            'code': code,
            'msg': msg
        }
        self.set_header("Content-Type", 'application/json')
        self.set_status(status)
        self.write(simplejson.dumps(error))
        self.finish()

    def get_location_city(self):
        header = self.request.headers
        real_ip = header.get("X-Real-IP", "0.0.0.0")
        (country, area, region, city, county, isp) = ip.parse_ip(real_ip)
        return city

    def validate(self, require_args):
        errors = []
        for require_arg in require_args:
            if not self.get_argument(require_arg, None):
                errors.append("%s is invalid" % require_arg)
        if len(errors):
            msg = " ".join(errors)
            logging.warning(msg)
            self.render_error(msg=msg)
            return False
        else:
            return True
