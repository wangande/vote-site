# -*- coding: utf-8 -*-

import setting
import tornado.gen
import tornado.web

from models.vote.vote_model import VoteModel
from basecore.routes import route
from services.vote_server import VoteService, VoteErrorException, VoteErrorCodeDefine
from views.admin.base import AdminAsyncAuthHandler
from util.urls import get_image_medium_url
from util import time_common


# 前端和后端请求参数映射，这样即使前端或后端修改参数名称，也不必修改逻辑代码
class AdminVoteReqParam(object):
    """admin get vote request param"""
    VOTE_ID = "vote_id"
    NAME = "name"
    AUTHOR = "author"
    SUMMARY = "summary"
    MD5 = "md5"
    PAGE = "page"
    PAGE_SIZE = "page_size"


# 前端和后端请求返回映射，这样即使前端或后端修改参数名称，也不必修改逻辑代码
class AdminVoteResponse(object):
    """admin get vote request response"""
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


@route(r"/admin/vote/list", name="admin.vote.list")
class AdminVoteListHandler(AdminAsyncAuthHandler):
    """admin get vote list"""
    template = "admin/vote/list.html"
    title = "admin vote list"
    vote_s = VoteService()

    @tornado.gen.engine
    def parse_vote_list(self, vote_list, callback=None):
        for vote in vote_list:
            vote[AdminVoteResponse.DATE] = time_common.timestamp_to_string(vote[VoteModel.date],
                                                                           time_common.FULL_PATTERN)
            vote[AdminVoteResponse.URL] = get_image_medium_url(vote[VoteModel.md5])

        callback(vote_list)

    @tornado.gen.engine
    def _get_(self):
        try:
            vote_id = self.get_argument(AdminVoteReqParam.VOTE_ID, "")
            name = self.get_argument(AdminVoteReqParam.NAME, "")
            author = self.get_argument(AdminVoteReqParam.AUTHOR, "")
            page = int(self.get_argument(AdminVoteReqParam.PAGE, 0))
            page_size = int(self.get_argument(AdminVoteReqParam.PAGE_SIZE, setting.PAGE_SIZE))

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
                AdminVoteResponse.VOTE_ID: vote_id,
                AdminVoteResponse.NAME: name,
                AdminVoteResponse.AUTHOR: author,
                AdminVoteResponse.PAGE: page,
                AdminVoteResponse.PAGE_SIZE: page_size,
                AdminVoteResponse.VOTE_LIST: vote_list,
                AdminVoteResponse.VOTE_TOTAL: vote_total,
            }

            self.render(**response)
        except VoteErrorException, e:
            self.render_error(msg=str(e))


@route(r"/admin/vote/edit", name="admin.vote.edit")
class AdminVoteEditHandler(AdminAsyncAuthHandler):
    template = "admin/vote/edit.html"
    title = "admin vote edit"
    vote_s = VoteService()

    @tornado.gen.engine
    def parse_vote(self, vote, callback=None):

        vote[AdminVoteResponse.DATE] = time_common.timestamp_to_string(vote[VoteModel.date],
                                                                       time_common.FULL_PATTERN)
        vote[AdminVoteResponse.URL] = get_image_medium_url(vote[VoteModel.md5])

        callback(vote)

    @tornado.gen.engine
    def _get_(self):
        try:
            vote_id = self.get_argument(AdminVoteReqParam.VOTE_ID, "")
            vote = yield tornado.gen.Task(self.vote_s.get_vote, vote_id)
            vote = yield tornado.gen.Task(self.parse_vote, vote)
            response = {
                AdminVoteResponse.VOTE_ID: vote_id,
                AdminVoteResponse.VOTE_INFO: vote,
            }
            self.render(**response)
        except VoteErrorException, e:
            self.render_error(msg=str(e))

    @tornado.gen.engine
    def _post_(self):
        try:
            name = self.get_argument(AdminVoteReqParam.NAME, "")
            author = self.get_argument(AdminVoteReqParam.AUTHOR, "")
            summary = self.get_argument(AdminVoteReqParam.SUMMARY, "")
            md5 = self.get_argument(AdminVoteReqParam.MD5, "")

            if not name:
                raise VoteErrorException(VoteErrorCodeDefine.VOTE_NAME_NULL)

            if not author:
                raise VoteErrorException(VoteErrorCodeDefine.VOTE_AUTHOR_NULL)

            if not summary:
                raise VoteErrorException(VoteErrorCodeDefine.VOTE_SUMMARY_NULL)

            if not md5:
                raise VoteErrorException(VoteErrorCodeDefine.VOTE_MD5_NULL)

            new_vote = {
                VoteModel.name: name,
                VoteModel.author: author,
                VoteModel.summary: summary,
                md5: md5,
            }
            yield tornado.gen.Task(self.vote_s.add_vote, new_vote)
            self.render_success(data=new_vote)
        except VoteErrorException, e:
            self.render_error(msg=str(e))

    @tornado.gen.engine
    def _put_(self):
        try:
            vote_id = self.get_argument(AdminVoteReqParam.VOTE_ID, "")
            name = self.get_argument(AdminVoteReqParam.NAME, "")
            author = self.get_argument(AdminVoteReqParam.AUTHOR, "")
            summary = self.get_argument(AdminVoteReqParam.SUMMARY, "")
            md5 = self.get_argument(AdminVoteReqParam.MD5, "")

            if not vote_id:
                raise VoteErrorException(VoteErrorCodeDefine.VOTE_ID_NULL)

            put_vote = {
                VoteModel.name: name,
                VoteModel.author: author,
                VoteModel.summary: summary,
                md5: md5,
            }
            yield tornado.gen.Task(self.vote_s.update_vote, vote_id, **put_vote)
            self.render_success(data=put_vote)
        except VoteErrorException, e:
            self.render_error(msg=str(e))

    @tornado.gen.engine
    def _delete_(self):
        try:
            vote_id = self.get_argument(AdminVoteReqParam.VOTE_ID, "")
            if not vote_id:
                raise VoteErrorException(VoteErrorCodeDefine.VOTE_ID_NULL)

            vote = yield tornado.gen.Task(self.vote_s.delete_vote, vote_id)
            self.render_success(data=vote)
        except VoteErrorException, e:
            self.render_error(msg=str(e))

