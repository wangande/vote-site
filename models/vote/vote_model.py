#!/usr/bin/env python
# -*- coding: utf-8 -*-


from basecore.models import AsyncBaseModel


class VoteModel(AsyncBaseModel):
    """vote model"""

    table = "vote"
    key = "vote_id"

    name = "name"
    summary = "summary"
    ballot = "ballot"
    author = "author"
    md5 = "md5"
    date = "date"


class VoteStatsModel(AsyncBaseModel):
    """Vote Stats Model"""

    table = "vote_stats"
    key = "vote_stats_id"

    vote_id = "vote_id"
    ip = "ip"



