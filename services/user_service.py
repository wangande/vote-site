#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib

import tornado.gen
import tornado.httpclient

from services.base import BaseService, BaseErrorException
from models.user.admin_model import AdminModel

__all__ = ['AdminService']


class UserErrorCodeDefine(object):
    """错误码定义"""
    NOT_USER_NAME = 0x0001
    NOT_USER_MAIL = 0x0002
    NOT_PASSWORD = 0x0003
    NOT_CONFIRM_PASSWORD = 0x0004
    NOT_USER_NAME_OR_PASSWORD = 0x0005
    USER_NAME_ERROR = 0x0006
    PASSWORD_ERROR = 0x0007
    USER_NAME_OR_PASSWORD_ERROR = 0x0008
    TOW_PASSWORDS_NOT_IDENTICAL = 0x0009

    USER_EXISTS = 0x0010
    USER_NOT_EXISTS = 0x0011


# 错误码对应的错误信息
User_Error_Code_MAP = {
    UserErrorCodeDefine.NOT_USER_NAME: "No Username",
    UserErrorCodeDefine.NOT_USER_MAIL: "No Mail",
    UserErrorCodeDefine.NOT_PASSWORD: "No Password",
    UserErrorCodeDefine.NOT_CONFIRM_PASSWORD: "Not Confirm Password",
    UserErrorCodeDefine.NOT_USER_NAME_OR_PASSWORD: "No username or password",
    UserErrorCodeDefine.USER_NAME_ERROR: "User Name Error",
    UserErrorCodeDefine.PASSWORD_ERROR: "Password Error",
    UserErrorCodeDefine.USER_NAME_OR_PASSWORD_ERROR: "Username or Password Error",
    UserErrorCodeDefine.TOW_PASSWORDS_NOT_IDENTICAL: "The two passwords are not identical",
    UserErrorCodeDefine.USER_EXISTS: "User Exists",
    UserErrorCodeDefine.USER_NOT_EXISTS: "User Not Exists",
}


class UserErrorException(BaseErrorException):

    def __repr__(self):
        msg = User_Error_Code_MAP.get(self.error_code, '')
        return "[*] Error:%s > %s. module: %s, class: %s, method: %s, line: %s " % (self.error_code, msg,
                                                                                    self.module_name,
                                                                                    self.class_name,
                                                                                    self.method_name,
                                                                                    self.line_no)

    def __str__(self):
        return User_Error_Code_MAP.get(self.error_code, 'not find any match msg for code:%s' % self.error_code)


class AdminService(BaseService):
    """admin service"""
    admin_m = AdminModel()

    @tornado.gen.engine
    def one(self, admin_id=None, mail=None, callback=None):
        query = {}
        if admin_id:
            query[AdminModel.admin_id] = admin_id
        if mail:
            query[AdminModel.mail] = mail

        admin = yield tornado.gen.Task(self.admin_m.find_one, query)
        callback(admin)

    @tornado.gen.engine
    def login(self, mail, password, callback=None):
        query = {
            AdminModel.mail: mail
        }
        admin = yield tornado.gen.Task(self.admin_m.find_one, query)
        if not admin:
            raise UserErrorException(UserErrorCodeDefine.USER_NOT_EXISTS)

        password_md5 = hashlib.md5(password).hexdigest()

        if admin["password"] != password_md5:
            raise UserErrorException(UserErrorCodeDefine.USER_NAME_OR_PASSWORD_ERROR)

        callback(admin)

    @tornado.gen.engine
    def register(self, mail, password, callback=None):
        query = {
            AdminModel.mail: mail
        }
        admin = yield tornado.gen.Task(self.admin_m.find_one, query)
        if admin:
            raise UserErrorException(UserErrorCodeDefine.USER_EXISTS)

        password_md5 = hashlib.md5(password).hexdigest()
        new_admin = {
            AdminModel.mail: mail,
            AdminModel.password: password_md5,
            AdminModel.if_use: 1
        }

        admin_id = yield tornado.gen.Task(self.admin_m.insert, new_admin)
        callback(admin_id)
