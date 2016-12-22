#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: andrew
@date: 2016-9-28
@description: admin requests base define
"""

import urlparse
import simplejson
import tornado.web
import tornado.gen
import setting
import datetime

from views.base import RequestHandler

ADMIN_LOGIN_TIME_COOKIE_KEY = 'admintlg'
ADMIN_KEEP_LOGIN_SECONDS = 30 * 60


class AdminHandler(RequestHandler):

    def initialize(self):
        self.session.SESSION_ID_NAME = 'VOTE_TORNADO_ID'
        super(AdminHandler, self).initialize()

    @property
    def get_login_url(self):
        return '/admin/user/login'

    @property
    def get_logout_url(self):
        return '/admin/user/logout'

    def render_error(self, status=203, code=203, msg=''):
        error = {
            'status': 'error',
            'code': code,
            'msg': msg,
        }
        self.set_status(status)
        self.set_header("Content-Type", 'application/json')
        self.write(simplejson.dumps(error))
        self.finish()

    def render_success(self, status=200, code=203, msg='', data=""):
        success = {
            'status': 'success',
            'code': code,
            'msg': msg,
            'data': data,
        }
        self.set_status(status)
        self.set_header("Content-Type", 'application/json')
        self.write(simplejson.dumps(success))
        self.finish()

    def render(self, **kwargs):
        self.response.update(kwargs)
        RequestHandler.render(self, **self.response)

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


class AdminAsyncAuthHandler(AdminHandler):
    """
        该类全部需要用户权限，并且集成session功能，
        所以子类不能使用@tornado.web.authenticated,
        需要非用户权限请使用RequestHandler
    """
    """
        覆盖get,post,put,delete方法，全部使用异步阻塞，
        子类使用_{method}_方法，并且在执行完时加上self.finish() 
        需要加上的原因是子类可能也需要执行异步阻塞，
        如果父类调用sele.finish()则子类将不能使用connection
    """
    admin_info = None

    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self, *args, **kwargs):
        if not hasattr(self, '_get_'):
            raise tornado.web.HTTPError(405)

        session_expired = yield tornado.gen.Task(self.is_session_expired)
        if session_expired:  # for session_expired anti-moth 20160106
            return

        admin_info = yield tornado.gen.Task(self.session.get, 'admin_info')
        has_priv = self.check_priv(admin_info)
        if not has_priv:
            if self.request.method in ('GET', 'HEAD'):
                url = self.get_login_url
                if '?' not in url:
                    if urlparse.urlsplit(url).scheme:
                        next_url = self.request.full_url()
                    else:
                        next_url = self.request.uri
                url += "?next=" + next_url
                self.redirect(url)
                return

        self.admin_info = admin_info
        self._get_(*args, **kwargs)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self, *args, **kwargs):
        if not hasattr(self, '_post_'):
            raise tornado.web.HTTPError(405)

        session_expired = yield tornado.gen.Task(self.is_session_expired)
        if session_expired:  # for session_expired anti-moth 20160106
            return

        admin_info = yield tornado.gen.Task(self.session.get, 'admin_info')
        has_priv = self.check_priv(admin_info)
        if not has_priv:
            raise tornado.web.HTTPError(403)

        self.admin_info = admin_info
        self._post_(*args, **kwargs)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def put(self, *args, **kwargs):
        if not hasattr(self, '_put_'):
            raise tornado.web.HTTPError(405)

        session_expired = yield tornado.gen.Task(self.is_session_expired)
        if session_expired:  # for session_expired anti-moth 20160106
            return

        admin_info = yield tornado.gen.Task(self.session.get, 'admin_info')
        has_priv = self.check_priv(admin_info)
        if not has_priv:
            raise tornado.web.HTTPError(403)

        self.admin_info = admin_info
        self._put_(*args, **kwargs)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def delete(self, *args, **kwargs):
        if not hasattr(self, '_delete_'):
            raise tornado.web.HTTPError(405)

        session_expired = yield tornado.gen.Task(self.is_session_expired)
        if session_expired:  # for session_expired anti-moth 20160106
            return

        admin_info = yield tornado.gen.Task(self.session.get, 'admin_info')
        has_priv = self.check_priv(admin_info)
        if not has_priv:
            raise tornado.web.HTTPError(403)

        self.admin_info = admin_info
        self._delete_(*args, **kwargs)

    def render(self, **kwargs):
        kwargs['is_login'] = True
        kwargs['admin_info'] = self.admin_info
        AdminHandler.render(self, **kwargs)

    def check_priv(self, admin_info):
        has_priv = False
        if admin_info:
            has_priv = True

        return has_priv

    @tornado.gen.engine
    def is_session_expired(self, callback=None):  # for session_expired anti-moth 20160106
        login_time = self.get_cookie(ADMIN_LOGIN_TIME_COOKIE_KEY)

        # 后台审核时的跳转。进行后台登录验证检查。若成立则延期会话过期时间或伪造编辑平台登录时间。editorinfo的伪造在 /admin的handler中处理
        # anti-moth 20160108
        if login_time is None:
            redirect_url = self.get_logout_url
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # /web/resource/state 的10s定时请求
                self.set_header('Content-Type', 'application/json; charset=UTF-8')
                self.write(simplejson.dumps({'success': False, 'status': 302,
                                             'redirect': redirect_url,  'msg': 'session_expired'}))
                self.finish()
            else:
                self.redirect(redirect_url)
            callback(True)
            return

        if not self.request.uri.startswith("/admin/status"):
            # 修改过期时间的计算方式，浏览器采用0时区的时间。  anti-moth 20160107
            # new_expires = datetime.datetime.fromtimestamp(time.time() + SDK_WEB_KEEP_LOGIN_SECONDS)
            new_expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=ADMIN_KEEP_LOGIN_SECONDS)
            self.set_cookie(ADMIN_LOGIN_TIME_COOKIE_KEY, login_time, expires=new_expires)

        callback(False)


class ListBaseHandler(AdminAsyncAuthHandler):
    def _get_(self):
        self.pageNum = int(self.get_argument("pageNum", 1))
        self.numPerPage = int(self.get_argument("numPerPage", setting.PAGE_SIZE))
        self.options = dict()
        self.options["pageNum"] = self.pageNum
        self.options["numPerPage"] = self.numPerPage

    def _post_(self):
        self.options = {}
        self.pageNum = int(self.get_argument("pageNum", 1))
        self.numPerPage = int(self.get_argument("numPerPage", 20))

        orderField = self.get_argument("orderField", None)
        orderDirection = self.get_argument("orderDirection", None)

        self.pos = (self.pageNum - 1) * self.numPerPage
        self.sorts = []

        argOrderDirection = setting.ASC
        if orderDirection:
            if orderDirection == "asc":
                argOrderDirection = setting.ASC
            else:
                argOrderDirection = setting.DESC

        if orderField:
            self.sorts = [
                [orderField, argOrderDirection]
            ]

        self.options["pageNum"] = self.pageNum
        self.options["numPerPage"] = self.numPerPage
        self.options["pageNum"] = self.pageNum

        if orderField:
            self.options["orderField"] = orderField
        if orderDirection:
            self.options["orderDirection"] = orderDirection
