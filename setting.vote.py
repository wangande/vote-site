# -*- coding: utf-8 -*-
import os
import pymongo
from tornado.options import define


# 指向易讯运用的group
DEFAULT_GROUP_NAME = 'groupyx'
APPS_BASE_PATH = 'apps'
DEFAULT_APP_ID = '5268b93b602ede779f92501e'
CORE_APP_NAME = 'yixun'
NEED_SYNC = False
SITE_URL = "10.0.1.125:12345"
MEDIA_BASE_URL = "http://10.0.1.125:9000"
ELA_LOGGING_URL = 'http://10.0.1.120:8080/api/v1/proxy/namespaces/kube-system/services/elasticsearch-logging/'
YIXUN_RES_LOG_NODE = "9c1d480bf998a21f44de5baea669a0fa_node0"


STATIC_USE_CDN_FLAG = False

STATIC_CDN_URL = "http://7xi53e.com1.z0.glb.clouddn.com"

APP_NAMES = {}

DESC = pymongo.DESCENDING
ASC = pymongo.ASCENDING
PAGE_SIZE = 20

# image size

IMAGE_LARGE_EDGE = 1024
IMAGE_MEDIUM_WIDTH = 320
IMAGE_MEDIUM_HEIGHT = 480

IMAGE_LARGE_SIZE = 1024
IMAGE_CARD_SIZE = 640
IMAGE_AR_SIZE = 480
IMAGE_MEDIUM_SIZE = 320
IMAGE_SMALL_SIZE = 200
IMAGE_SYX_LOGO_SIZE = 160
IMAGE_TINY_SIZE = 100
IMAGE_SMALLEST_SIZE = 50

# support file ext
EXT_PIC_LIST = ["jpg", "png", "jpeg", "gif"]
EXT_VIDEO_LIST = ["mp4", "flv", "wmv", "m4v", "f4v"]
EXT_AUDIO_LIST = ["mp3", "ogg"]
EXT_3D_LIST = ["unity3d", "obj", "dae"]
FILE_TYPE_EQ_EXTS = ['unity3d', 'tracker_data',
                     'data', 'dat', 'xml', 'mp3', 'ipa', 'zip', 'fbx']

NOT_RESIZE_FILE_TYPES = [
    'audio', 'tracker_data', 'data', 'dat', 'xml', 'mp3', 'ipa']
NOT_WAIT_RESIZE_BACKS = [
    'audio', 'tracker_data', 'data', 'dat', 'xml', 'mp3', 'ipa']


REDIS_HOST = os.getenv("REDIS_MASTER_PORT_6379_TCP_ADDR", '10.0.1.37')
REDIS_PORT = int(os.getenv("REDIS_MASTER_PORT_6379_TCP_PORT", 6379))
REDIS_SESSIONS = 10

# mongo
MONGO_HOST = os.getenv("MONGODB_PORT_5672_TCP_ADDR", "127.0.0.1")
MONGO_PORT = int(os.getenv("MONGODB_PORT_6379_TCP_PORT", 27017))
MONGO_USER = os.getenv("MONGODB_USERNAME", "mongo")
MONGO_PASS = os.getenv("MONGODB_PASSWORD", "wangande")
