# -*- coding: utf-8 -*-

import logging
import tornado.web
import setting

from tornado.options import options
from tornado import locale

from pycket.session import SessionMixin

from basecore.routes import route


class RequestHandler(tornado.web.RequestHandler, SessionMixin):

    def initialize(self):
        self.redis_client = options.get('redis_client', None)
        if not self.redis_client:
            logging.error('need redis_client in tornado.options')

    def static_url(self, path, include_host=None, use_cdn=None):
        self.require_setting("static_path", "static_url")
        static_handler_class = self.settings.get(
            "static_handler_class", tornado.web.StaticFileHandler)

        if use_cdn is None:
            use_cdn = setting.STATIC_USE_CDN_FLAG

        if include_host is None:
            include_host = getattr(self, "include_host", False)

        if use_cdn:
            base = setting.STATIC_CDN_URL
        elif include_host:
            base = self.request.protocol + "://" + self.request.host
        else:
            base = ""
        return base + static_handler_class.make_static_url(self.settings, path)

    def prepare(self):
        self.view_permission = -1
        self.edit_permission = -1

    def get_user_locale(self):
        if hasattr(self, "lan_form_arg"):
            lan = self.lan_form_arg
        else:
            lan = self.get_secure_cookie("user_locale")
        self.__locale = lan
        print lan
        if not lan:
            bl = self.get_browser_locale()
            bl_code = bl.code

            print bl_code
            self.__locale = bl_code
            self.set_secure_cookie("user_locale", bl_code)
            return bl
        return locale.get(lan)
    # def init_locale(self):
    #     lan = self.get_secure_cookie("user_locale")
    #     if not lan:
    #         lan = 'zh_CN'
    #         self.set_secure_cookie("user_locale", lan)
    #     self.__locale = lan

    def get_lan(self):
        return self.__locale

    def _(self, text):
        """ Localisation shortcut """
        return self.locale.translate(text).encode("utf-8")

    def _u(self, text):
        return self.locale.translate(text)

    def render(self, **kwargs):
        render_title = self.title if hasattr(self, 'title') else ''
        template_in_core = self.template_in_core if hasattr(self, 'template_in_core') else False
        title = self._(render_title)
        template = self.template if hasattr(self, 'template') else (
            self.__class__.template if hasattr(self.__class__, 'template') else "")

        # 增加公共参数
        kwargs['site_url'] = setting.SITE_URL
        kwargs['isset'] = self.isset
        kwargs['make_url'] = self.make_url
        kwargs['get_comma'] = self.get_comma

        self.namespace = kwargs
        tornado.web.RequestHandler.render(self, template, title=title, lan=self.__locale, **kwargs)
    """ will to template  """

    def isset(self, v):
        return self.namespace.has_key(v)

    def make_url(self, url, **kwargs):
        return url

    def get_comma(self, code, **kwargs):
        lan = self.get_secure_cookie("user_locale")
        if code == 'comma':
            if lan == 'zh_CN':
                return '，'
            elif lan == 'ja_JP':
                return '、'
            elif lan == 'en_US':
                return ', '
        elif code == 'stop':
            if lan == 'zh_CN':
                return '、'
            elif lan == 'ja_JP':
                return '、'
            elif lan == 'en_US':
                return ', '
        return ''

    @property
    def app_name(self):
        return None

    @property
    def base_file_path(self):
        return self.application.base_file_path

    def get_browser_locale(self, default="en_US"):
        """Determines the user's locale from Accept-Language header.

        See http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.4
        """
        if "Accept-Language" in self.request.headers:
            languages = self.request.headers["Accept-Language"].split(",")
            locales = []
            for language in languages:
                parts = language.strip().split(";")
                if len(parts) > 1 and parts[1].startswith("q="):
                    try:
                        score = float(parts[1][2:])
                    except (ValueError, TypeError):
                        score = 0.0
                else:
                    score = 1.0
                locales.append((parts[0], score))
            if locales:
                locales.sort(key=lambda (l, s): s, reverse=True)
                codes = [self._true_code(l[0]) for l in locales]
                return locale.get(*codes)
        return locale.get(default)

    def _true_code(self, code):
        if code == 'zh':
            return 'zh_CN'
        elif code == 'ja':
            return 'ja_JP'
        elif code == 'en':
            return 'en_US'
        else:
            return code

    def get_request_ip(self):
        header = self.request.headers
        real_ip = header.get("X-Real-IP", "0.0.0.0")
        return real_ip


@route(r"/(.*)", name="error")
class ErrorHandler(RequestHandler):

    def prepare(self):
        super(RequestHandler, self).prepare()
        self.set_status(404)
        raise tornado.web.HTTPError(404)


class ErrorHandlerStatusCode(object):
    Not_Found = 404
    Server_Error = 500
    Server_Bad_Gateway = 502

ErrorHandlerStatusCodeMsg = {
    ErrorHandlerStatusCode.Not_Found: "Not Found",
    ErrorHandlerStatusCode.Server_Error: "Server Error",
    ErrorHandlerStatusCode.Server_Bad_Gateway: "Server Bad Gateway",
}


class PageNotFoundHandler(tornado.web.RequestHandler):
    """Generates an error response with status_code for all requests."""

    def initialize(self, status_code):
        self.set_status(status_code)

    def prepare(self):
        logging.error(self._status_code)

        if self._status_code == ErrorHandlerStatusCode.Not_Found:
            error_msg = ErrorHandlerStatusCodeMsg[ErrorHandlerStatusCode.Not_Found]
        elif self._status_code == ErrorHandlerStatusCode.Server_Bad_Gateway:
            error_msg = ErrorHandlerStatusCodeMsg[ErrorHandlerStatusCode.Server_Bad_Gateway]
        else:
            error_msg = ErrorHandlerStatusCodeMsg[ErrorHandlerStatusCode.Server_Error]

        # response = {
        #     "error_msg": error_msg,
        # }
        # self.render("error.html", **response)
        # raise HTTPError(self._status_code)
        self.write("HTTPError:{}".format(error_msg))
        self.finish()

tornado.web.ErrorHandler = PageNotFoundHandler
