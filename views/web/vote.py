#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setting

import tornado.gen
import tornado.web

from models.vote.vote_model import VoteModel
from basecore.routes import route
from services.vote_server import VoteService, VoteErrorException, VoteErrorCodeDefine
from views.web.base import WebHandler
from util.urls import get_image_medium_url
from util import time_common


# 前端和后端请求参数映射，这样即使前端或后端修改参数名称，也不必修改逻辑代码
class WebVoteReqParam(object):
    """web get vote request param"""
    VOTE_ID = "vote_id"
    NAME = "name"
    AUTHOR = "author"
    SUMMARY = "summary"
    MD5 = "md5"
    PAGE = "page"
    PAGE_SIZE = "page_size"


# 前端和后端请求返回映射，这样即使前端或后端修改参数名称，也不必修改逻辑代码
class WebVoteResponse(object):
    """web get vote request response"""
    VOTE_ID = "vote_id"
    NAME = "name"
    AUTHOR = "author"
    PAGE = "page"
    PAGE_SIZE = "page_size"
    DATE = "date"
    VOTE_LIST = "vote_list"
    VOTE_TOTAL = "vote_total"
    VOTE_INFO = "vote_info"
    URL = "url"


@route(r"/web/vote/list", name="web.vote.list")
class WebBallotListHandler(WebHandler):
    """web get vote list"""
    template = "web/vote/list.html"
    title = "web vote list"
    vote_s = VoteService()

    @tornado.gen.engine
    def parse_vote_list(self, vote_list, callback=None):
        for vote in vote_list:
            vote[WebVoteResponse.DATE] = time_common.timestamp_to_string(vote[VoteModel.date],
                                                                           time_common.FULL_PATTERN)
            vote[WebVoteResponse.URL] = get_image_medium_url(vote[VoteModel.md5])

        callback(vote_list)

    @tornado.gen.engine
    def _get_(self):
        try:
            vote_id = self.get_argument(WebVoteReqParam.VOTE_ID, "")
            name = self.get_argument(WebVoteReqParam.NAME, "")
            author = self.get_argument(WebVoteReqParam.AUTHOR, "")
            page = int(self.get_argument(WebVoteReqParam.PAGE, 0))
            page_size = int(self.get_argument(WebVoteReqParam.PAGE_SIZE, setting.PAGE_SIZE))

            _conditions = {}
            if vote_id:
                _conditions[VoteModel.key] = vote_id
            if name:
                _conditions[VoteModel.name] = name
            if author:
                _conditions[VoteModel.author] = author

            _query = self.vote_s.parse_page(page, page_size)
            _query["conditions"] = _conditions
            vote_list = yield tornado.gen.Task(self.vote_s.get_vote_list, _conditions)
            vote_list = yield tornado.gen.Task(self.parse_vote_list, vote_list)
            vote_total = yield tornado.gen.Task(self.vote_s.get_vote_total, _conditions)

            response = {
                WebVoteResponse.VOTE_ID: vote_id,
                WebVoteResponse.NAME: name,
                WebVoteResponse.AUTHOR: author,
                WebVoteResponse.PAGE: page,
                WebVoteResponse.PAGE_SIZE: page_size,
                WebVoteResponse.VOTE_LIST: vote_list,
                WebVoteResponse.VOTE_TOTAL: vote_total,
            }

            self.render(**response)
        except VoteErrorException, e:
            self.render_error(msg=str(e))


class WeBallotReqParam(object):
    VOTE_ID = "vote_id"


class WebBallotResponse(object):
    VOTE_ID = "vote_id"
    VOTE_INFO = "vote_info"


@route(r"/web/vote/ballot", name="web.vote.ballot")
class WebVoteBallotHandler(WebHandler):
    title = "vote ballot"
    vote_s = VoteService()

    @tornado.gen.engine
    def _post_(self):
        try:
            vote_id = self.get_argument(WeBallotReqParam.VOTE_ID, "")
            if not vote_id:
                raise VoteErrorException(VoteErrorCodeDefine.VOTE_ID_NULL)

            real_ip = self.get_request_ip()
            vote = yield tornado.gen.Task(self.vote_s.add_ballot, vote_id, real_ip)
            self.render_success(data=vote)
        except VoteErrorException, e:
            self.render_error(msg=str(e))
