#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

import tornado.gen
import tornado.web

from models.files.file_model import FileModel
from services.base import BaseService, BaseErrorException


__all__ = ["FileErrorException", "FilesService"]


class FileErrorCodeDefine(object):
    """错误码定义"""
    FILE_EXISTS = 0x0001
    FILE_NOT_EXISTS = 0x0002


# 错误码对应的错误信息
File_Error_Code_MAP = {
    FileErrorCodeDefine.FILE_EXISTS: "File Exists",
    FileErrorCodeDefine.FILE_NOT_EXISTS: "File Not Exists",
}


class FileErrorException(BaseErrorException):

    def __repr__(self):
        msg = File_Error_Code_MAP.get(self.error_code, '')
        return "[*] Error:%s > %s. module: %s, class: %s, method: %s, line: %s " % (self.error_code, msg,
                                                                                    self.module_name,
                                                                                    self.class_name,
                                                                                    self.method_name,
                                                                                    self.line_no)

    def __str__(self):
        return File_Error_Code_MAP.get(self.error_code, 'not find any match msg for code:%s' % self.error_code)


class FilesService(BaseService):
    file_m = FileModel()

    @tornado.gen.engine
    def get_file_data(self, md5, callback):
        query = {
            self.file_m.md5: md5,
        }
        file_data = yield tornado.gen.Task(self.file_m.find_one, query)
        if not file_data:
            raise FileErrorException(FileErrorCodeDefine.FILE_NOT_EXISTS)
        callback(file_data)

    @tornado.gen.engine
    def update_file_data(self, file_md5, file_id, callback):
        query = {
            "md5": file_md5,
        }
        update_set = {
            "$set": {
                "file_id": file_id,
            }
        }
        flg = yield tornado.gen.Task(self.file_m.update, query, update_set, upsert=True, safe=True)
        callback(flg)

    @tornado.gen.engine
    def upload_image_file(self, content, fdfs_client, callback):

        md5 = uuid.uuid1().get_hex()

        file_id = fdfs_client.upload_by_buffer(md5, content)

        yield tornado.gen.Task(self.update_file_data, md5, file_id)
        callback(None)
