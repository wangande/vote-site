#!/usr/bin/env python
# -*- coding: utf-8 -*-

from basecore.models import AsyncBaseModel


class AdminModel(AsyncBaseModel):
    """admin model"""

    table = 'admin'
    key = 'admin_id'

    admin_id = "admin_id"
    mail = "mail"
    password = "password"
    if_use = 'if_use'


class AdminRoleModel(AsyncBaseModel):
    """admin role model"""

    # meta
    table = 'admin_role'
    key = 'admin_role_id'

    admin_role_id = "admin_role_id"
    name = "name"
    permission = "permission"
