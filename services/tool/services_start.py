#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import fcntl
import struct
import logging

from tornado.options import options


class ServicesStart(object):

    def __init__(self, back):
        self.back = back

    def _get_ip_address_(self, eth_name):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,
            struct.pack('256s', eth_name[:15])
        )[20:24])

    def start_services(self):
        cur_ip = self._get_ip_address_('eth0')
        logging.error('current server address: {}:{}'.format(cur_ip, options.port))
        if self.back:
            self.back()
