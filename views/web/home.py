#!/usr/bin/env python
# -*- coding: utf-8 -*-


import tornado.gen
import tornado.web

from basecore.routes import route
from views.web.base import WebHandler


@route("/", name="index")
@route("/web", name="web")
class HomeIndexHandler(WebHandler):
    title = "Home"
    template = "web/index.html"
    nav_active = "Home"

    @tornado.gen.engine
    def _get_(self):
        self.render()
