#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.gen
import urllib2
import simplejson
import logging
from models.ip.ip_model import IpAreaModle, IpIndexModle


class IpService(object):
    ip_index_m = IpIndexModle()
    ip_area_m = IpAreaModle()

    def make_bin_to_eight_bit(self, old_bin):
        """
        将二进制执法串补成八位，如100补成00000100
        :param old_bin: 旧的二进制字符串
        :return: 八位二进制字符串
        """
        new_bin = old_bin

        if len(old_bin) < 8:
            add_num = 8 - len(old_bin)

            for i in xrange(0, add_num):
                new_bin = '0' + new_bin

        return new_bin

    def make_ip_add_one(self, old_ip):
        """
        如果IP的位的值为255，向前一位进1,该位置0
        :param old_ip:
        :return:
        """
        net_ip = old_ip.split('.')
        if int(net_ip[3]) + 1 == 256:
            net_ip[3] = str(0)

            if int(net_ip[2]) + 1 == 256:
                net_ip[2] = str(0)

                if int(net_ip[1]) + 1 == 256:
                    net_ip[1] = str(0)
                    net_ip[0] = str(int(net_ip[0]) + 1)
                else:
                    net_ip[1] = str(int(net_ip[1])+1)
            else:
                net_ip[2] = str(int(net_ip[2]) + 1)
        else:
            net_ip[3] = str(int(net_ip[3]) + 1)

        new_ip = '.'.join(net_ip)

        return new_ip

    def make_ip_to_index(self, ip):
        """
        将ip转成数字
        :param ip: ip地址
        :return: ip索引
        """
        if not ip:
            return 0

        ip_bit = ip.split('.')
        ip_str = ''
        for v in ip_bit:
            tmp_str = bin(int(v))[2:]
            tmp_ip_str = self.make_bin_to_eight_bit(tmp_str)
            ip_str += tmp_ip_str

        return int(ip_str, 2)

    @tornado.gen.engine
    def find_ip_index(self, query, callback=None):
        ip_index = yield tornado.gen.Task(self.ip_index_m.find_one, query)
        callback(ip_index)

    @tornado.gen.engine
    def find_area_index(self, query, callback=None):
        ip_area = yield tornado.gen.Task(self.ip_area_m.find_one, query)
        callback(ip_area)

    @tornado.gen.engine
    def select_ip_info(self, ip, callback=None):
        area = {
            'country': '',      # 国家
            'province': '',     # 省份
            'city': '',         # 城市
            'address': '',      # 地址
            'isp': '',          # 网络提供商
            'Longitude': '',    # 经度
            'Latitude': '',     # 纬度
            'timezone': '',     # 时区
            'uct': ''           # 时区
        }
        index = self.make_ip_to_index(ip)
        if index:
            query = {
                "end_index": {"$gte": index},
                "start_index": {"$lte": index}
            }
            ip_index = yield tornado.gen.Task(self.find_ip_index, query)
            if ip_index:
                query = {
                    "index": ip_index.get('Area_index', 0)
                }

                ip_area = yield tornado.gen.Task(self.find_area_index, query)
                if ip_area:
                    area['country'] = ip_area.get('country', '')
                    area['province'] = ip_area.get('province', '')
                    area['city'] = ip_area.get('city', '')
                    area['address'] = ip_area.get('address', '')
                    area['isp'] = ip_area.get('isp', '')
                    area['Longitude'] = ip_area.get('Longitude', '')
                    area['Latitude'] = ip_area.get('Latitude', '')
                    area['timezone'] = ip_area.get('timezone', '')
                    area['uct'] = ip_area.get('uct', '')

        callback(area)

    @tornado.gen.engine
    def get_network_area_from_taobao(self, client_ip, callback=None):
        """
        通过ip从淘宝接口获取网络地域和网络运营商
        :param client_ip:
        :param callback:
        :return:网络运营商和地域
        """
        try:
            timeout = 3
            url = "http://ip.taobao.com/service/getIpInfo.php?ip=" + client_ip
            res = urllib2.urlopen(url, timeout=timeout).read()
            res_data = simplejson.loads(res)
            if int(res_data['code']) == 0:
                data = res_data['data']
                area = [
                    data.get('country', '').encode('utf-8'),
                    data.get('area', '').encode('utf-8'),
                    data.get('region', '').encode('utf-8'),
                    data.get('city', '').encode('utf-8'),
                ]
                # area.append(data.get('country', '').encode('utf-8'))
                # area.append(data.get('area', '').encode('utf-8'))
                # area.append(data.get('region', '').encode('utf-8'))
                # area.append(data.get('city', '').encode('utf-8'))
                area = '-'.join(area)
                net = data.get('isp', '').encode('utf-8')
                callback((net, area))
            else:
                logging.error("(%s) get net and area error:%s", client_ip, res_data['data'])
                callback((None, None))

        except Exception, e:
            callback((None, None))