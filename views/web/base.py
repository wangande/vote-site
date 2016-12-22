# -*- coding: utf-8 -*-

"""
@author: andrew
"""

import traceback
import logging
import datetime
import simplejson
import urlparse
import tornado.web
import tornado.gen

from views.base import RequestHandler
from tornado.web import HTTPError

WEB_LOGIN_TIME_COOKIE_KEY = 'webtlg'
WEB_KEEP_LOGIN_SECONDS = 60 * 60
WEB_LOGIN_REDIS_KEY_BASE = "webrdslg"


class WebHandler(RequestHandler):
    web_info = None

    def initialize(self):
        self.session.SESSION_ID_NAME = 'VOTE_TORNADO_ID'
        super(WebHandler, self).initialize()

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, ,PUT, DELETE')
        self.set_header('Access-Control-Max-Age', 1000)
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Content-type', 'application/json')

    @property
    def get_login_url(self):
        return '/web/user/login'

    @property
    def get_logout_url(self):
        return '/web/user/logout'

    def render(self, **kwargs):
        nav_active = self.__class__.nav_active if hasattr(self.__class__, 'nav_active') else None

        # nav_active = self.nav if hasattr(self, 'nav') else ''
        kwargs['nav_active'] = nav_active
        self.response.update(kwargs)
        RequestHandler.render(self, **self.response)

    def render_error(self, status=203, code=0, msg=''):
        error = {
            'status': 'error',
            'msg': msg,
            'code': code
        }
        self.set_header("Content-Type", 'application/json')
        self.set_status(status)
        self.write(simplejson.dumps(error))
        self.finish()

    def render_success(self, status=200, code=1, msg='', data=''):
        success = {
            'status': 'success',
            'code': code,
            'msg': msg,
            'data': data,
        }
        self.set_header("Content-Type", 'application/json')
        self.set_status(status)
        self.write(simplejson.dumps(success))
        self.finish()

    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self, *args, **kwargs):
        if not hasattr(self, '_get_'):
            raise tornado.web.HTTPError(405)
        self._get_(*args, **kwargs)

        # try:
        #     if not hasattr(self, '_get_'):
        #         raise tornado.web.HTTPError(405)
        #     self._get_(*args, **kwargs)
        # except HTTPError, e:
        #
        #     self.write("HTTPError:{}".format(e.status_code))
        #     self.finish()
        # except Exception, e:
        #     traceback.print_exc()
        #     self.write("server error:{}".format(""))
        #     self.finish()

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


class WebAsyncAuthHandler(WebHandler):

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

    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self, *args, **kwargs):
        if not hasattr(self, '_get_'):
            raise tornado.web.HTTPError(405)

        session_expired = yield tornado.gen.Task(self.is_session_expired)
        if session_expired:  # for session_expired anti-moth 20160106
            return
        self.web_info = yield tornado.gen.Task(self.session.get, 'web_info')
        has_priv = self.check_priv(self.web_info)
        if not has_priv:
            if self.request.method in ('GET', 'HEAD'):
                url = self.get_login_url
                if '?' not in url:
                    if urlparse.urlsplit(url).scheme:
                        next_url = self.request.full_url()
                    else:
                        next_url = self.request.uri
                url = url + "?next=" + next_url
                self.redirect(url)
                return
        login_redis_expired = yield tornado.gen.Task(self.is_login_redis_expired)
        if login_redis_expired:
            return

        self._get_(*args, **kwargs)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self, *args, **kwargs):
        if not hasattr(self, '_post_'):
            raise tornado.web.HTTPError(405)
        session_expired = yield tornado.gen.Task(self.is_session_expired)
        if session_expired:
            return
        self.web_info = yield tornado.gen.Task(self.session.get, 'web_info')
        has_priv = self.check_priv(self.web_info)
        if not has_priv:
            raise tornado.web.HTTPError(403)

        login_redis_expired = yield tornado.gen.Task(self.is_login_redis_expired)
        if login_redis_expired:  \
            return

        self._post_(*args, **kwargs)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def put(self, *args, **kwargs):
        if not hasattr(self, '_put_'):
            raise tornado.web.HTTPError(405)
        session_expired = yield tornado.gen.Task(self.is_session_expired)
        if session_expired:
            return

        self.web_info = yield tornado.gen.Task(self.session.get, 'web_info')
        has_priv = self.check_priv(self.sdkeditorinfo)
        if not has_priv:
            raise tornado.web.HTTPError(403)

        login_redis_expired = yield tornado.gen.Task(self.is_login_redis_expired)
        if login_redis_expired:
            return

        self._put_(*args, **kwargs)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def delete(self, *args, **kwargs):
        if not hasattr(self, '_delete_'):
            raise tornado.web.HTTPError(405)
        session_expired = yield tornado.gen.Task(self.is_session_expired)
        if session_expired:
            return

        self.web_info = yield tornado.gen.Task(self.session.get, 'web_info')
        has_priv = self.check_priv(self.web_info)
        if not has_priv:
            raise tornado.web.HTTPError(403)

        login_redis_expired = yield tornado.gen.Task(self.is_login_redis_expired)
        if login_redis_expired:
            return

        self._delete_(*args, **kwargs)

    def render(self, **kwargs):
        if self.web_info:
            kwargs['is_login'] = True
        else:
            kwargs['is_login'] = False
        kwargs['web_info'] = self.web_info
        WebHandler.render(self, **kwargs)

    def check_priv(self, web_info):
        has_priv = True
        if not web_info:
            has_priv = False
            return has_priv

        return has_priv

    @tornado.gen.engine
    def is_session_expired(self, callback=None):
        login_time = self.get_cookie(WEB_LOGIN_TIME_COOKIE_KEY)

        if login_time is None:
            redirect_url = self.get_logout_url + "?next=" + self.request.uri
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # /web/resource/state 的10s定时请求
                self.set_header('Content-Type', 'application/json; charset=UTF-8')
                self.write(simplejson.dumps({'success': False, 'status': 302,
                                             'redirect': redirect_url,  'msg': 'session_expired'}))

                self.finish()
            else:
                self.redirect(redirect_url)
            callback(True)
            return

        if not self.request.uri.startswith("/web/status"):

            # 修改过期时间的计算方式，浏览器采用0时区的时间。  anti-moth 20160107
            # new_expires = datetime.datetime.fromtimestamp(time.time() + SDK_WEB_KEEP_LOGIN_SECONDS)
            new_expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=WEB_KEEP_LOGIN_SECONDS)
            self.set_cookie(WEB_LOGIN_TIME_COOKIE_KEY, login_time, expires=new_expires)

        callback(False)

    @tornado.gen.engine
    def is_login_redis_expired(self, callback=None):  # for session_expired anti-moth 20160106
        web_login_key = WEB_LOGIN_REDIS_KEY_BASE + self.web_info["editor_id"]
        web_login_expired = yield tornado.gen.Task(self.redis_client.get, web_login_key)

        if not web_login_expired:
            redirect_url = self.get_logout_url + "?next=" + self.request.uri
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # /web/resource/state 的10s定时请求
                self.set_header('Content-Type', 'application/json; charset=UTF-8')
                self.write(simplejson.dumps({'success': False, 'status': 302,
                                             'redirect': redirect_url,  'msg': 'session_expired'}))

                self.finish()
            else:
                self.redirect(redirect_url)
            callback(True)
            return

        if not self.request.uri.startswith("/sdk/web/status"):

            yield tornado.gen.Task(self.redis_client.set, web_login_key, self.web_info["editor_id"])
            yield tornado.gen.Task(self.redis_client.expire, web_login_key, WEB_KEEP_LOGIN_SECONDS)

        callback(False)
