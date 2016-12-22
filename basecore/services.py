#!/usr/bin/env python
# -*- coding: utf-8 -*-

SERVICE_TOOL = 'tool'
SERVICE_TYPE_INIT = 0


class Service:
    def __init__(self, name, service):
        self.name = name
        self.service = service

    def __str__(self):
        return self.name + self.service


class NoServiceException(Exception):
    pass


class InitService(object):
    """
    Example
    -------

    @service(name = "someModel",type=SERVICE_TYPE_COMMON)
    class SomeModel():
        pass

    services = service.get_service(service_name)


    """
    _init_service_list = []

    def __init__(self, name=None, type=SERVICE_TYPE_INIT):
        self.name = name
        self._type = type

    def __call__(self, _service):
        """gets called when we class decorate"""
        name = self.name and self.name or _service.__name__
        name = name.lower()

        self._init_service_list.append({"name": name, "service": _service})
        return _service

    @classmethod
    def load_init_services(cls):
        for init_service in cls._init_service_list:
            init_service['service']()  # class __init__
