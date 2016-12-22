#!/usr/bin/env python
# -*- coding: utf-8 -*-


import tornado.gen
import tornado.httpclient

from services.base import BaseService, BaseErrorException
from models.vote.vote_model import VoteModel, VoteStatsModel

__all__ = ['VoteService']

VOTE_IP_BALLOT_TAIL = "_vote_ip_ballot_tail"
VOTE_IP_BALLOT_EXPIRE = 60*60


class VoteErrorCodeDefine(object):
    """错误码定义"""

    VOTE_NAME_NULL = 0x0001
    VOTE_AUTHOR_NULL = 0x0002
    VOTE_SUMMARY_NULL = 0x0003
    VOTE_MD5_NULL = 0x0004
    VOTE_ID_NULL = 0x0005

    VOTE_DATA_ERROR = 0x0011
    VOTE_DATA_EXISTS = 0x0012
    VOTE_NOT_EXISTS = 0x0013
    IP_LAST_BALLOT = 0x0014


# 错误码对应的错误信息
Vote_Error_Code_MAP = {
    VoteErrorCodeDefine.VOTE_NAME_NULL: "VOTE_NAME_NULL",
    VoteErrorCodeDefine.VOTE_AUTHOR_NULL: "VOTE AUTHOR NULL",
    VoteErrorCodeDefine.VOTE_SUMMARY_NULL: "VOTE SUMMARY NULL",
    VoteErrorCodeDefine.VOTE_MD5_NULL: "VOTE MD5 NULL",
    VoteErrorCodeDefine.VOTE_ID_NULL: "VOTE ID NULL",
    VoteErrorCodeDefine.VOTE_DATA_ERROR: "VOTE DATA ERROR",
    VoteErrorCodeDefine.VOTE_DATA_EXISTS: "VOTE DATA EXISTS",
    VoteErrorCodeDefine.VOTE_NOT_EXISTS: "VOTE NOT EXISTS",
    VoteErrorCodeDefine.IP_LAST_BALLOT: "IP_LAST_BALLOT",
}


class VoteErrorException(BaseErrorException):
    def __repr__(self):
        msg = Vote_Error_Code_MAP.get(self.error_code, '')
        return "[*] Error:%s > %s. module: %s, class: %s, method: %s, line: %s " % (self.error_code, msg,
                                                                                    self.module_name,
                                                                                    self.class_name,
                                                                                    self.method_name,
                                                                                    self.line_no)

    def __str__(self):
        return Vote_Error_Code_MAP.get(self.error_code, 'not find any match msg for code:%s' % self.error_code)


class VoteService(BaseService):
    """vote service"""
    vote_m = VoteModel()
    vote_stats_m = VoteStatsModel()

    @tornado.gen.engine
    def add_vote(self, new_vote, callback=None):
        if not new_vote.get(VoteModel.name) or new_vote.get(VoteModel.summary) or new_vote.get(
                VoteModel.author) or new_vote.get(VoteModel.md5):
            raise VoteErrorException(VoteErrorCodeDefine.VOTE_DATA_ERROR)

        query = {
            VoteModel.name: new_vote[VoteModel.name]
        }
        vote = yield tornado.gen.Task(self.vote_m.find_one, query)
        if vote:
            raise VoteErrorException(VoteErrorCodeDefine.VOTE_DATA_ERROR)

        new_vote[VoteModel.ballot] = 0
        vote_id = yield tornado.gen.Task(self.vote_m.insert, new_vote)
        callback(vote_id)

    @tornado.gen.engine
    def delete_vote(self, vote_id, callback=None):
        query = {
            VoteModel.key: vote_id
        }
        vote = yield tornado.gen.Task(self.vote_m.find_one, query)
        if not vote:
            raise VoteErrorException(VoteErrorCodeDefine.VOTE_NOT_EXISTS)

        yield tornado.gen.Task(self.vote_m.delete, {VoteModel.key: vote_id})
        callback(vote)

    @tornado.gen.engine
    def update_vote(self, vote_id, **kwargs):
        query = {
            VoteModel.key: vote_id
        }
        vote = yield tornado.gen.Task(self.vote_m.find_one, query)
        if not vote:
            raise VoteErrorException(VoteErrorCodeDefine.VOTE_NOT_EXISTS)

        update_args = {}

        if kwargs.get(VoteModel.name):
            update_args[VoteModel.name] = kwargs[VoteModel.name]

        if kwargs.get(VoteModel.author):
            update_args[VoteModel.author] = kwargs[VoteModel.author]

        if kwargs.get(VoteModel.ballot):
            update_args[VoteModel.ballot] = kwargs[VoteModel.ballot]

        if kwargs.get(VoteModel.md5):
            update_args[VoteModel.md5] = kwargs[VoteModel.md5]

        if update_args:
            yield tornado.gen.Task(self.vote_m.update, {VoteModel.key: vote_id},
                                   {"$set": update_args})

        kwargs["callback"](None)

    @tornado.gen.engine
    def check_last_ip_ballot(self, ip, callback=None):
        vote_ip_ballot_key = ip + VOTE_IP_BALLOT_TAIL
        vote_ip_ballot_key_rs = yield tornado.gen.Task(self.redis_client.exists, vote_ip_ballot_key)
        if not vote_ip_ballot_key_rs:
            yield tornado.gen.Task(self.redis_client.set, vote_ip_ballot_key, ip)
            yield tornado.gen.Task(self.redis_client.expire, vote_ip_ballot_key, VOTE_IP_BALLOT_EXPIRE)
            callback(True)

        callback(False)

    @tornado.gen.engine
    def add_vote_stats(self, vote_id, ip, callback=None):
        new_vote_stats = {
            VoteStatsModel.vote_id: vote_id,
            VoteStatsModel.ip: ip,
        }

        vote_stats_id = yield tornado.gen.Task(self.vote_stats_m.insert, new_vote_stats)
        callback(vote_stats_id)

    @tornado.gen.engine
    def add_ballot(self, vote_id, ip, callback=None):
        query = {
            VoteModel.key: vote_id
        }
        vote = yield tornado.gen.Task(self.vote_m.find_one, query)
        if not vote:
            raise VoteErrorException(VoteErrorCodeDefine.VOTE_NOT_EXISTS)

        last_ip_ballot = yield tornado.gen.Task(self.check_last_ip_ballot, ip)
        if not last_ip_ballot:
            raise VoteErrorException(VoteErrorCodeDefine.IP_LAST_BALLOT)

        ballot = vote.get(VoteModel.ballot, 0) + 1
        update_args = {
            VoteModel.ballot: ballot,
        }
        yield tornado.gen.Task(self.update_vote, vote_id, **update_args)

        yield tornado.gen.Task(self.add_vote_stats, vote_id, ip)
        vote[VoteModel.ballot] = ballot
        callback(vote)

    @tornado.gen.engine
    def get_vote_list(self, _query, callback=None):
        vote_list = yield tornado.gen.Task(self.vote_m.get_list, _query)
        callback(vote_list)

    @tornado.gen.engine
    def get_vote_total(self, **kwargs):
        vote_total = yield tornado.gen.Task(self.vote_m.count)
        kwargs["callback"](vote_total)

    @tornado.gen.engine
    def get_vote(self, vote_id, callback=None):
        query = {
            VoteModel.key: vote_id
        }
        vote = yield tornado.gen.Task(self.vote_m.find_one, query)
        if not vote:
            raise VoteErrorException(VoteErrorCodeDefine.VOTE_NOT_EXISTS)
        callback(vote)