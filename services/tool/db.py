#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import asyncmongo
from pymongo import Connection
from tornado.options import options

from basecore.services import InitService
from basecore.models import AsyncBaseModel
import setting


@InitService()
class Mongodb(object):
    """docstring for Mongodb"""

    def __init__(self):
        asyn_client = asyncmongo.Client(
            pool_id='isdb',
            host=setting.MONGO_HOST,
            port=setting.MONGO_PORT,
            dbuser=setting.MONGO_USER,
            dbpass=setting.MONGO_PASS,
            dbname='admin',
            maxcached=150,
            maxconnections=150,
        )
        connection = Connection(setting.MONGO_HOST, setting.MONGO_PORT)

        options["asyn_client"] = asyn_client
        AsyncBaseModel.configure(asyn_client)
        options["mono_conn"] = connection
        logging.error("{}".format("[init]Mongodb init success"))
