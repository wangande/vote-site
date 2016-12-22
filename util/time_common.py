#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from datetime import datetime

hour_seconds = 3600
day_seconds = hour_seconds * 24
week_seconds = day_seconds * 7
month_seconds = day_seconds * 30


FULL_PATTERN = "%Y-%m-%d %H:%M"
FULL_PATTERN2 = "%Y/%m/%d %H:%M"

NOYEAR_PATTERN = "%m-%d %H:%M"
DAY_PATTERN = "%Y-%m-%d"
HOURTIME_PATTERN = "%Y%m%d%H"
DAY_PATTERN2 = "%Y%m%d"

NOYEAR_DAY_PATTERN = "%m-%d"


def datetime_to_string(dt, pattern):
    return dt.strftime(pattern)


def string_to_datetime(s, pattern):
    return datetime.strptime(s, pattern)


def datetime_to_timestamp(dt):
    return int(time.mktime(dt.timetuple()))


# str -> seconds
def string_to_timestamp(s, pattern):
    return datetime_to_timestamp(string_to_datetime(s, pattern))


# seconds -> str
def timestamp_to_string(ts, pattern):
    return time.strftime(pattern, time.localtime(ts))
