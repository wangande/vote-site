#!/usr/bin/env python
# -*- coding: utf-8 -*-

from basecore.models import AsyncBaseModel


class IpIndexModle(AsyncBaseModel):
    """IP index model"""

    table = "ip_index"
    key = "ip_index_id"

    start_index = "start_index"
    end_index = "end_index"
    start_ip = "start_ip"
    end_ip = "end_ip"
    unknown = "unknown"
    Area_index = "Area_index"


class IpAreaModle(AsyncBaseModel):
    """Ip area model"""
    table = "ip_area"
    key = "ip_area_id"
    
    country = "country"      # 国家
    province = "province"    # 省份
    city = "city"         # 城市
    address = "address"      # 地址
    isp = "isp"          # 网络提供商
    Longitude = "Longitude"    # 经度
    Latitude = "Latitude"     # 纬度
    timezone = "timezone"     # 时区
    uct = "uct"          # 时区
    index = "index"        # ip索引
    info = "info"         # 原始ip信息
