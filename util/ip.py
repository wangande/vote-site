#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import IP


def process_data(jsondata):
    strs = jsondata.split('\t')
    country = ""
    province = ""
    city = ""
    isp = ""
    try:
        country = strs[0]
        province = strs[1]
        city = strs[2]
        isp = strs[3]
    except Exception, e:
        pass

    return (country, "", province, city, "", isp)


def parse_ip(ip):
    result = IP.find(ip)
    return process_data(result)


if __name__ == '__main__':
    address = parse_ip('111.222.233.123')
    print address
    logging.error(address)
