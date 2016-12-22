#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime

import tornado.web
import tornado.gen


from models.user.admin_model import AdminModel
from basecore.routes import route
from views.admin.base import AdminHandler, ADMIN_KEEP_LOGIN_SECONDS, ADMIN_LOGIN_TIME_COOKIE_KEY
from services.user_service import AdminService, UserErrorException, UserErrorCodeDefine


# 前端和后端请求参数映射，这样即使前端或后端修改参数名称，也不必修改逻辑代码
class AdminUserReqParam(object):
    """admin user request param"""
    USER_NAME = "user_name"
    USER_MAIl = "user_mail"
    MAIL = "mail"
    PASSWORD = "password"
    CONFIRM_PASSWORD = "password2"


# 前端和后端请求返回映射，这样即使前端或后端修改参数名称，也不必修改逻辑代码
class AdminUserResponse(object):
    """admin user request response"""
    USER_NAME = "user_name"
    USER_MAIl = "user_mail"
    MAIL = "MAIL"
    PASSWORD = "password"
    CONFIRM_PASSWORD = "password2"

    ADMIN_ID = "admin_id"
    ADMIN_INFO = "admin_info"
    REDIRECT_URL = "redirect_url"


@route(r'/admin/user/login', name='admin.user.login')
class AdminUserLoginHandler(AdminHandler):
    """admin user login"""
    title = 'User login'
    template = '/admin/user/login.html'
    admin_s = AdminService()

    @tornado.gen.engine
    def _get_(self):
        self.render()

    @tornado.gen.engine
    def _post_(self):
        try:
            mail = self.get_argument(AdminUserReqParam.MAIL, None)
            password = self.get_argument(AdminUserReqParam.PASSWORD, None)

            if not mail or not password:
                raise UserErrorException(UserErrorCodeDefine.NOT_USER_NAME_OR_PASSWORD)

            admin = yield tornado.gen.Task(self.admin_s.login, mail, password)
            admin_info = {
                AdminUserResponse.ADMIN_ID: admin[AdminModel.admin_id],
                AdminUserResponse.MAIL: admin[AdminModel.mail],
            }
            self.set_secure_cookie(AdminUserResponse.ADMIN_ID, str(admin[AdminModel.admin_id]), expires_days=1)
            yield tornado.gen.Task(self.session.set, AdminUserResponse.ADMIN_INFO, admin_info)

            # 设置会话超时标志
            login_time = time.time()
            login_expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=ADMIN_KEEP_LOGIN_SECONDS)
            self.set_cookie(ADMIN_LOGIN_TIME_COOKIE_KEY, "%d|%d" % (login_time % 5, login_time / 5), expires=login_expires)

            redirect_url = self.get_argument("next", '/admin')
            self.render_success(data={AdminUserResponse.REDIRECT_URL, redirect_url})
        except UserErrorException, e:
            self.render_error(msg=self._(str(e)))


@route(r"/admin/user/logout", name="admin.user.logout")
class AdminUserLogoutHandler(AdminHandler):
    """admin user logout"""
    @tornado.gen.engine
    def _get_(self):
        try:
            yield tornado.gen.Task(self.session.delete, AdminUserResponse.ADMIN_INFO)
            self.clear_cookie(AdminUserResponse.ADMIN_ID)
        except Exception, e:
            pass
        redirect_url = AdminHandler().get_login_url
        self.redirect(self.get_argument("next", redirect_url))


@route(r"/admin/user/register", name="admin.user.register")
class AdminUserRegisterHandler(AdminHandler):
    """admin user register"""
    title = 'user register'
    template = 'admin/user/register.html'
    admin_s = AdminService()

    @tornado.gen.engine
    def _get_(self):
        self.render()

    @tornado.gen.engine
    def _post_(self):
        try:
            mail = self.get_argument(AdminUserReqParam.MAIL, None)
            password = self.get_argument(AdminUserReqParam.PASSWORD, None)
            password2 = self.get_argument(AdminUserReqParam.CONFIRM_PASSWORD, None)

            if (not mail) or (not password) or (not password2):
                raise UserErrorException(UserErrorCodeDefine.NOT_USER_NAME_OR_PASSWORD)

            if password != password2:
                raise UserErrorException(UserErrorCodeDefine.TOW_PASSWORDS_NOT_IDENTICAL)

            yield tornado.gen.Task(self.admin_s.register, mail, password)

            data = {
                AdminUserResponse.MAIL: mail,
                AdminUserResponse.PASSWORD: password,
                AdminUserResponse.CONFIRM_PASSWORD: password2,
            }
            self.render_success(data=data)

        except UserErrorException, e:
            self.render_error(msg=self._(str(e)))
