#!/usr/bin/env python
# -*- coding: utf-8 -*-

from basecore.models import AsyncBaseModel


class FileModel(AsyncBaseModel):
    """File model"""

    table = 'files'
    key = '_id'

    file_id = "file_id"
    md5 = "md5"
    width = "width"
    height = "height"


