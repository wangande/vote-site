#!/usr/bin/env python
# -*- coding: utf-8 -*-

import traceback
import logging
import uuid
import os
import Image
import setting

import tornado.web
import tornado.gen


from basecore.routes import route
from views.admin.base import AdminAsyncAuthHandler
from models.files.file_model import FileModel

from util import urls
from util import md5
from util.tornado_qiniu_util import get_upload_token, tornado_upload_by_path

IMAGE_RESIZE_STATUS_SUCCESS = '200'
MUSIC_MAX_SIZE = 100 * 1024 * 1024  # 100M


@route(r"/admin/upload", name="admin.upload")
class AdminUploaderHandler(AdminAsyncAuthHandler):
    """文件上传"""

    file_model = FileModel()
    max_edge = setting.IMAGE_LARGE_EDGE
    mix_width = setting.IMAGE_MEDIUM_HEIGHT
    mix_heigth = setting.IMAGE_MEDIUM_HEIGHT

    def _get_(self):
        logging.error("please set method post")
        self.render_error(msg="please set method post")

    @tornado.gen.engine
    def _post_(self):
        try:
            self._parse_argument()

            if not self._check_type_status():
                return

            file_exists, err_state = yield tornado.gen.Task(self._check_and_upload)
            if file_exists:
                logging.error("file_exists %s %s\n" % (file_exists, err_state))
                self.render_error(msg="file_exists %s %s" % (file_exists, err_state))
                return
            elif err_state:
                self.set_status(500)
                self.finish()
                return

            self.insert_file()
            self.write_result()

        except Exception as e:
            logging.error(e.message)
            exc_msg = traceback.format_exc()
            logging.error(exc_msg)
            raise tornado.web.HTTPError(500)

    def _parse_argument(self):
        """获取请求文件参数"""
        self.upload_file = self.request.files.get("file", None)
        self.width = 0
        self.height = 0
        self.need_narrow = False

        if not self.upload_file:
            return

        self.upload_file = self.upload_file[0]
        self.file_name = self.upload_file.get('filename', None)
        self.file_type = self.get_file_type()
        self.file_md5 = uuid.uuid4().get_hex()
        self.file_buffer = self.upload_file.get("body")

        if self.file_buffer:
            file_path = "/tmp/" + self.file_md5 + self.ext
            with open(file_path, "wb") as f:
                f.write(self.file_buffer)

            if os.path.exists(file_path):
                self.file_md5 = md5.get_file_md5(file_path)
                self.file_path = file_path

    def _check_type_status(self):
        """验证文件类型状态"""
        if not self.upload_file:
            self.render_error(msg="File is error")
            return False

        if not self.file_type:
            self.render_error(msg="File type is error")
            return False

        if not self.check_ext():
            return False

        if self.file_type == 'image':
            if not self.get_width_height(self.file_path):
                return False

        # 如果需要限制图片大小
        if self.need_narrow and self.file_type == 'image':
            if not self.check_size():
                return False

        return True

    def get_width_height(self, file_path):
        if not os.path.exists(file_path):
            self.render_error("File not exists")
            return False

        img = Image.open(file_path)
        width = img.size[0]
        height = img.size[1]
        self.width = width
        self.height = height
        return True

    def check_size(self):
        """验证图片尺寸"""
        width = self.width
        height = self.height
        max_edge = width

        if height > width:
            max_edge = height
        if self.instance == 'layer_picture':
            if max_edge > self.max_edge:
                self.render_error(msg="Can upload image bigger than 1024")
                return False
        if (width < self.mix_width) and (height < self.mix_heigth):
            self.render_error(msg="Can upload image smaller than 480*480")
            return False
        else:
            return True

    @tornado.gen.engine
    def _check_and_upload(self, callback=None):
        """验证文件是否存在，如果已存在直接返回文件ID，否则上传新文件"""
        file_exists = False
        err_state = None
        self.file_md5 = self.file_md5 + "_" + self.ext
        self.file_key = self.file_md5 + "." + self.ext
        self.file_id = yield tornado.gen.Task(self.check_file_exists, self.file_md5)
        if self.file_id:
            logging.info("find %s exists, write_result" % self.file_id)
            file_exists = True
            if callback:
                callback(file_exists, err_state)
            return

        self.file_id = yield tornado.gen.Task(self.upload_file_to_qiniu, self.file_path, self.file_key)
        logging.info('file_id: %s' % self.file_id)
        if not self.file_id:
            logging.error('fastdfs_client error ')
            err_state = "upload error"
        if callback:
            callback(file_exists, err_state)

    @tornado.gen.engine
    def check_file_exists(self, file_md5, callback):
        query = {
            self.file_model.md5: file_md5,
        }
        file_id = None
        f = yield tornado.gen.Task(self.file_model.find_one, query)
        if f:
            file_id = f[self.file_model.file_id]
        callback(file_id)

    def get_file_type(self, file_ctype=None):
        """获取文件类型"""
        ext = self.file_name.split(".")[-1]
        ext = ext.lower()
        self.ext = ext
        file_type = None
        if self.ext in setting.EXT_PIC_LIST:
            file_type = "image"
        if self.ext in setting.EXT_VIDEO_LIST:
            file_type = "video"
        if self.ext in setting.EXT_3D_LIST:
            file_type = "3d"
        if self.ext in setting.FILE_TYPE_EQ_EXTS:
            file_type = self.ext

        return file_type

    @tornado.gen.engine
    def insert_file(self, new_file_id=None):
        self.file_model.need_sync = False
        query = {
           self.file_model.md5: self.file_md5,
        }
        f = {
            self.file_model.file_id: self.file_id,
        }
        if new_file_id:
            f[self.file_model.file_id] = new_file_id
        if self.width:
            f[self.file_model.width] = self.width
        if self.height:
            f[self.file_model.height] = self.height
        update_set = {
            "$set": f,
        }

        yield tornado.gen.Task(self.file_model.update, query, update_set, upsert=True, safe=True)
        logging.error("insert_file success")

    def check_ext(self):
        """验证文件格式"""
        if self.file_type == 'image' and (self.ext not in setting.EXT_PIC_LIST):
            self.render_error(msg="文件类型[%s]不被支持，仅支持图片:%s" %
                                  (self.ext, setting.EXT_PIC_LIST))
            return False
        if self.file_type == 'video' and (self.ext not in setting.EXT_VIDEO_LIST):
            self.render_error("文件类型[%s]不被支持，仅支持视频:%s" %
                              (self.ext, setting.EXT_VIDEO_LIST))
            return False
        if self.file_type == '3d' and (self.ext not in setting.EXT_3D_LIST):
            self.render_error("文件类型[%s]不被支持，仅支持;3d模型:%s" %
                              (self.ext, setting.EXT_3D_LIST))
            return False
        return True

    @tornado.gen.engine
    def upload_file_to_qiniu(self, file_path, file_name, callback=None):
        file_key = ""
        try:
            token = get_upload_token(file_name)

            http_proxy = {}
            if hasattr(setting, 'qn_http_proxy'):
                http_proxy = setting.qn_http_proxy

            [ret, info] = yield tornado.gen.Task(tornado_upload_by_path, token, file_path, file_name,
                                                 http_proxy=http_proxy)

            logging.error("ret:%s" % ret)
            logging.error("info:%s" % info)
            if info.status_code == 200:  # 文件上传成功
                file_key = ret['hash']
            elif info.status_code == 614:  # 文件资源已存在
                file_key = file_name

        except Exception, e:
            logging.error("upload file to qiniu error")

        callback(file_key)

    def write_result(self):
        result = dict()
        result["status"] = "success"
        result["image_src"] = urls.get_image_large_url(self.file_md5)
        result["medium_image_src"] = urls.get_image_medium_url(self.file_md5)
        result["extend_widget_image"] = urls.get_image_url_by_size(self.file_md5, 480)
        result["small_image_src"] = urls.get_image_small_url(self.file_md5)
        result["tiny_image_src"] = urls.get_image_tiny_url(self.file_md5)
        result["file_id"] = self.file_id
        result["file_name"] = self.file_name
        result["md5"] = self.file_md5
        result['width'] = self.width
        result['height'] = self.height

        self.render_success(data=result)
