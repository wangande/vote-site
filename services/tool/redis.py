#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import setting
import tornadoredis

from tornado.options import options

from basecore.services import InitService


CONNECTION_POOL = tornadoredis.ConnectionPool(max_connections=100,
                                              wait_for_available=True,
                                              host=setting.REDIS_HOST, port=setting.REDIS_PORT)


@InitService()
class Redis(object):
    def __init__(self):
        options['redis_client'] = tornadoredis.Client(connection_pool=CONNECTION_POOL)
        logging.error("{}".format("[init]redis_client init success"))
