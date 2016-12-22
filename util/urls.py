#!/usr/bin/env python
# -*- coding: utf-8 -*-

from util.tornado_qiniu_util import BUCKETS_URL
import setting

image_large_size = setting.IMAGE_LARGE_SIZE
image_ar_size = setting.IMAGE_AR_SIZE
image_medium_size = setting.IMAGE_MEDIUM_SIZE
image_small_size = setting.IMAGE_SMALL_SIZE
image_tiny_size = setting.IMAGE_TINY_SIZE
image_smallest_size = setting.IMAGE_SMALLEST_SIZE
image_syx_logo_size = setting.IMAGE_SYX_LOGO_SIZE


def get_image_large_url(md5):
    return get_qiniu_image_url_by_size(md5)


def get_image_medium_url(md5, app_name=None, need_resize=False):
    return get_qiniu_image_url_by_size(md5, image_medium_size, app_name=app_name, need_resize=need_resize)


def get_image_small_url(md5, app_name=None, need_resize=False):

    return get_qiniu_image_url_by_size(md5, image_small_size, app_name=app_name, need_resize=need_resize)


def get_image_tiny_url(md5, app_name=None, need_resize=False):
    return get_qiniu_image_url_by_size(md5, image_tiny_size, app_name=app_name, need_resize=need_resize)


def get_image_smallest_url(md5, app_name=None, need_resize=False):
    return get_qiniu_image_url_by_size(md5, image_smallest_size, app_name=app_name, need_resize=need_resize)


def get_image_large_jpg_url(md5, app_name=None, need_resize=False):
    return get_qiniu_image_url_by_size(md5, dest_format="jpg", app_name=app_name, need_resize=need_resize)


def get_image_ar_jpg_url(md5, app_name=None, need_resize=False):
    return get_qiniu_image_url_by_size(md5, image_ar_size, dest_format="jpg", app_name=app_name, need_resize=need_resize)


def get_image_medium_jpg_url(md5, need_resize=False):
    return get_qiniu_image_url_by_size(md5, image_medium_size, dest_format="jpg", need_resize=need_resize)


def get_image_small_jpg_url(md5, need_resize=False):
    return get_qiniu_image_url_by_size(md5, image_small_size, dest_format="jpg", need_resize=need_resize)


def get_image_tiny_jpg_url(md5, need_resize=False):
    return get_qiniu_image_url_by_size(md5, image_tiny_size, dest_format="jpg", need_resize=need_resize)


def get_image_smallest_jpg_url(md5, need_resize=False):
    return get_qiniu_image_url_by_size(md5, image_smallest_size, dest_format="jpg", need_resize=need_resize)


def get_file_ext(md5):
    if md5:
        temp_list = md5.split("_")
        if len(temp_list) == 1:
            return None
        return temp_list[1]
    return None


def get_qiniu_image_url_by_size(md5, weight=0, height=0, x=0, y=0,
                                ext=None, dest_format=None, app_name="site", need_resize=False):

    ext_from_md5 = get_file_ext(md5)
    if not ext:
        ext = ext_from_md5
    if 'gif' == ext_from_md5 and ext != ext_from_md5:
        ext = ext_from_md5
    if not ext:
        ext = "jpg"

    qn_key = md5 + "." + ext

    base_src = BUCKETS_URL.get(app_name, BUCKETS_URL[app_name])
    if not need_resize:
        return "%s%s" % (base_src, qn_key)

    image_param = ""
    if weight == "full":
        weight = 0
    if height == "full":
        height = 0
    if weight or height:
        if x or y:
            weight = weight if weight else height
            height = height if height else weight
            image_param = "?imageMogr2/crop/!%sx%sa%sa%s" % (weight, height, x, y)
        else:
            image_param = "?imageView2/0/w/%s/h/%s" % (weight, height)

    if dest_format:
        if ext == "gif":
            dest_format = "gif"

        if image_param:
            image_param += "/format/%s" % dest_format
        else:
            image_param = "?imageMogr2/format/%s" % dest_format

    return "%s%s%s" % (base_src, qn_key, image_param)

