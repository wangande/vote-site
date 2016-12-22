#!/usr/bin/env python
# -*- coding:utf-8 -*-

import hashlib
import os


def get_str_md5(src):
    md5obj = hashlib.md5()
    md5obj.update(src)
    md5 = md5obj.hexdigest()
    return md5


# 大文件的MD5值
def get_file_md5(filename):
    if not os.path.isfile(filename):
        return None

    md5obj = hashlib.md5()
    f = file(filename, 'rb')
    while True:
        b = f.read(8096)
        if not b:
            break
        md5obj.update(b)
    f.close()

    md5 = md5obj.hexdigest()
    return md5


def calc_sha1(file_path):
    with open(file_path, 'rb') as f:
        sha1obj = hashlib.sha1()
        sha1obj.update(f.read())
        return sha1obj.hexdigest()


def calc_md5(file_path):
    with open(file_path, 'rb') as f:
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        return md5obj.hexdigest()


if __name__ == "__main__":
    print get_str_md5("xxxxxxxxxxxxxxxxx")
    print get_file_md5("./elasticsearch-logging.py")
