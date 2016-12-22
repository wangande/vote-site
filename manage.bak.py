# -*- coding: UTF-8 -*-

import os.path
import setting

import tornado.httpserver
import tornado.ioloop
import tornado.web

from ctypes import cdll
from basecore.routes import route
from basecore.services import InitService

from tornado.options import define, options
from tornadomail.backends.smtp import EmailBackend

define("port", default=3001, help="Run server on a specific port", type=int)


# 自定义Application类，继承于Application
class Application(tornado.web.Application):

    def __init__(self):
        def init():
            InitService.load_init_services()
            # 导入views，生成routes
            import views
            handlers = route.get_routes()
            # 定义setting，对tornado.web.Application进行设置
            settings = dict(
                blog_title=u"webar",
                template_path=os.path.join(os.path.dirname(__file__),
                                           "templates"),
                static_path=os.path.join(os.path.dirname(__file__), "static"),
                debug=True,
                cookie_secret="NyM8vWu0Slec0GLonsdI3ebBX0VEqU3Vm8MsHiN5rrc=",
                app_secret="XOJOwYhNTgOTJqnrszG3hWuAsTmVz0GisOCY6R5d1E8=",
                login_url="/",
                autoescape=None,
                gzip=True,
            )
            # redis配置
            redis_setting = {
                'host': setting.REDIS_HOST,
                'port': setting.REDIS_PORT,
                'db_sessions': setting.REDIS_SESSIONS,
            }
            # session配置为redis存储
            settings['session'] = {
                'engine': 'redis',
                'storage': redis_setting
            }

            tornado.web.Application.__init__(self, handlers, **settings)

        from services.tool.services_start import ServicesStart
        ServicesStart(back=init).start_services()

    @property
    def mail_connection(self):
        return EmailBackend(
            setting.mail_smtp,
            setting.mail_port,
            setting.mail_mail,
            setting.mail_passwd,
            True
        )

    @property
    def base_file_path(self):
        return os.path.dirname(__file__)


def main():
    options.log_to_stderr = True
    options.logging = 'info'
    tornado.options.parse_command_line()
    # 启动http server监听端口
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    # 设置本地化
    tornado.locale.set_default_locale("zh_CN")
    tornado.locale.load_translations(
        os.path.join(os.path.dirname(__file__), "translations")
    )
    # 启动ioloop
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
