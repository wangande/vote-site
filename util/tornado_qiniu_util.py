#!/usr/bin/env python
# -*- coding: utf-8 -*-


import setting
import logging
import tornadoqiniu
import mimetypes
import qiniu
import tornado.gen
import tornado.web

ACCESS_KEY = setting.QN_ACCESS_KEY
SECRET_KEY = setting.QN_SECRET_KEY

BUCKETS = setting.QN_BUCKETS
BUCKETS_URL = setting.QN_BUCKETS_URL


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


qiniuAuth = tornadoqiniu.Auth(ACCESS_KEY, SECRET_KEY)
qiniu_bucket_manager = qiniu.BucketManager(qiniuAuth)


def get_upload_token(filename, app_id="site"):
    """
    从七牛获取上传token，用于客户端请求上传,服务器端自主上传到七牛
    :param filename: 文件ming
    :param app_id: app id
    :return:
    """
    bucket = BUCKETS[app_id]
    expires = 3600
    policy = {}
    strict_policy = True
    # ext = filename.split(".")[-1]
    key = None

    token = qiniuAuth.upload_token(bucket, key=key, expires=expires, policy=policy, strict_policy=strict_policy)
    return token


# 使用文件路径上传
# 如果文件大小大于4m，自动断点续传
# 如果文件名已存在将返回错误
@tornado.gen.engine
def tornado_upload_by_path(token, file_path, filename=None, http_proxy={}, callback=None):

    content_type = get_content_type(file_path)
    [ret, info] = yield tornado.gen.Task(tornadoqiniu.put_file, token, filename, file_path,
                                         mime_type=content_type, check_crc=True, http_proxy=http_proxy)
    callback([ret, info])


# 使用文件流的方式上传文件
@tornado.gen.engine
def tornado_upload_by_stream(token, file_name, data, file_size=None, file_key=None, http_proxy={}, callback=None):
    mime_type = get_content_type(file_name)
    logging.error("mime_type:%s" % mime_type)

    [ret, info] = yield tornado.gen.Task(tornadoqiniu.put_data, token, file_key, data,
                                         mime_type=mime_type, check_crc=True, http_proxy=http_proxy)
    callback([ret, info])



