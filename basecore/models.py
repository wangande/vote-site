#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setting
import logging
import time
import cPickle
import simplejson
import pymongo
import tornado.gen
import traceback

from bson.objectid import ObjectId


__all__ = ['exist', 'unique', 'get', 'get_list', "get_list_all", 'find_one', 'count', 'insert', 'delete']

MONGODB_ID = "_id"
DELETE_FLAG = 'delete_flag'  # '1' 已经删除，'0'或者没有该字段表示没有删除
DEFAULT_SORT = [[MONGODB_ID, pymongo.DESCENDING, ], ]
QUERY_DONE = "--QUERY_DONE--"
QUERY_COLLECT = True


class ModelException(Exception):
    pass


class AsyncBaseModel(object):
    need_sync = setting.NEED_SYNC

    @classmethod
    def configure(cls, client):
        cls.async_client = client

    def __init__(self):
        if not hasattr(self, "async_client"):
            raise NotImplementedError("Must configure an async_client.")
        self.className = self.__class__.__name__
        self.module = self.__module__
        if hasattr(self, 'db'):
            db = self.db
        else:
            db = self.module.split('.')[1]

        if hasattr(self, 'table'):
            table = self.table
        else:
            table = self.className.lower()

        if hasattr(self, 'key'):
            key = self.key
        else:
            key = table + '_id'

        self._db_ = db
        self._table_ = table

        self.dao = self.async_client.connection(table, db)
        self._key_ = key

    def exist(self, query, callback):
        one = self.find_one(query)
        if one:
            callback(True)
        else:
            callback(False)

    def unique(self, query, callback=None):
        one = self.find_one(query)
        if one:
            callback(False)
        else:
            callback(True)

    def get(self, value, key=None, callback=None):
        if not key:
            key = self._key_
        callback(self.find_one({key: value}))

    def _id_convert(self, res, mongo_id_key):
        if MONGODB_ID in res:
            res[mongo_id_key] = str(res.pop(MONGODB_ID))
        else:
            logging.error("-*-mongoQueryError:noMongoId-*- result: %s, self._key_: %s " % (str(res), self._key_))
        return res

    @tornado.gen.engine
    def do_query(self, spec, fields=None, pos=0, count=0, sorts=DEFAULT_SORT, callback=None):
        if QUERY_COLLECT:
            logging.info("mongoQueryCollect: %s, %s, %s", self._db_, self._table_,
                         simplejson.dumps(spec, default=convert_to_builtin_type))
        result_list, error = yield tornado.gen.Task(self.dao.find, spec=spec,
                                                    fields=fields, limit=count, skip=pos, sort=sorts)

        _id_convert = self._id_convert
        _key = self._key_
        callback([_id_convert(res, _key) for res in result_list[0]])

        del result_list[0][:]
        result_list = None

    @tornado.gen.engine
    def get_all_docs(self, query, fields=None, pos=0, count=0, sorts=DEFAULT_SORT, include_del=False, callback=None):
        """
        此方法慎用，建议在service层或逻辑层自己分页查询。且逻辑业务应紧跟查询结果，尽量减小暂存容器对象的规模。
        ！！在大数据量时，列表的extend会造成内存不断迁移，导致python持有数个巨型列表，内存使用增加而得不到及时释放。
        """
        spec = dict(query)
        _key = self._key_
        sorts = [[x if x != _key else MONGODB_ID for x in y] for y in sorts]
        if not include_del:
            spec[DELETE_FLAG] = {'$ne': '1'}
        if QUERY_COLLECT:
            logging.info("mongoQueryCollect: %s, %s, %s", self._db_, self._table_,
                         simplejson.dumps(spec, default=convert_to_builtin_type))
        if _key in spec:
            spec[MONGODB_ID] = spec.pop(_key)

        if fields and _key in fields:
            fields[MONGODB_ID] = fields.pop(_key)

        response_list = []
        query_pos = int(pos)
        need_count = int(count)

        per_query_num = need_count or 40000
        while True:

            temps = yield tornado.gen.Task(self.do_query, spec, fields, query_pos, per_query_num, sorts)
            if not temps:
                break

            response_list.extend(temps)

            _cur_count = len(temps)
            del temps[:]
            if need_count > 0:
                if need_count > _cur_count:
                    need_count -= _cur_count
                    query_pos += _cur_count
                else:
                    break
            else:
                query_pos += _cur_count

        callback(response_list)
        del response_list[:]
        response_list = None

    @tornado.gen.engine
    def get_all(self, query={}, callback=None):
        response_list = []
        conditions = {}
        fields = {}
        sorts = []
        count = 39999
        if "conditions" in query:
            conditions = query["conditions"]
        if "fields" in query:
            fields = query["fields"]
        if "sorts" in query:
            sorts = query["sorts"]
        if 'conditions' not in query:
            conditions = query
        # date_sort_flg = False
        # add conditon delete_flag is not 1
        conditions[DELETE_FLAG] = {'$ne': '1'}
        if QUERY_COLLECT:
            logging.info("mongoQueryCollect: %s, %s, %s", self._db_, self._table_,
                         simplejson.dumps(conditions, default=convert_to_builtin_type))
        sorts = [[x if x != self._key_ else MONGODB_ID for x in y] for y in sorts]
        if not sorts:
            sorts.append([MONGODB_ID, pymongo.DESCENDING])
        if self._key_ in conditions:
            conditions[MONGODB_ID] = conditions[self._key_]
            del conditions[self._key_]
        if self._key_ in fields:
            fields[MONGODB_ID] = fields[self._key_]
            del fields[self._key_]
        if not fields.keys():
            fields = None
        result_list, error = yield tornado.gen.Task(self.dao.find, spec=conditions,
                                                    fields=fields, sort=sorts, limit=count)
        del conditions[DELETE_FLAG]
        # result_list = result_list[0]
        # for result in result_list:
        #     if MONGODB_ID in result:
        #         result[self._key_] = str(result[MONGODB_ID])
        #         del result[MONGODB_ID]
        #     response_list.append(result)
        # callback(response_list)
        _id_convert, _key = self._id_convert, self._key_
        callback([_id_convert(res, _key) for res in result_list[0]])

    @tornado.gen.engine
    def get_list_all(self, query={}, callback=None):
        response_list = []
        conditions = {}
        fields = {}
        sorts = []
        pos = 0
        count = 39999
        if "conditions" in query:
            conditions = query["conditions"]
        if "pos" in query:
            pos = query["pos"]
        if "count" in query:
            count = query["count"]
        if "fields" in query:
            fields = query["fields"]
        if "sorts" in query:
            sorts = query["sorts"]
        if 'conditions' not in query:
            conditions = query
        if QUERY_COLLECT:
            logging.info("mongoQueryCollect: %s, %s, %s", self._db_, self._table_,
                         simplejson.dumps(conditions, default=convert_to_builtin_type))
        sorts = [[x if x != self._key_ else MONGODB_ID for x in y] for y in sorts]
        if not sorts:
            sorts.append([MONGODB_ID, pymongo.DESCENDING])

        pos = int(pos)
        count = int(count)
        if self._key_ in conditions:
            conditions[MONGODB_ID] = conditions[self._key_]
            del conditions[self._key_]
        if self._key_ in fields:
            fields[MONGODB_ID] = fields[self._key_]
            del fields[self._key_]
        if not fields.keys():
            fields = None
        result_list, error = yield tornado.gen.Task(self.dao.find, spec=conditions,
                                                    fields=fields, limit=count, skip=pos, sort=sorts)
        # result_list = result_list[0]
        # for result in result_list:
        #     try:
        #         if MONGODB_ID in result:
        #             result[self._key_] = str(result[MONGODB_ID])
        #             del result[MONGODB_ID]
        #         response_list.append(result)
        #     except Exception, e:
        #         logging.error(e.message)
        #         logging.error("result: %s, self._key_: %s " % (str(result), self._key_))
        #
        # callback(response_list)
        _id_convert, _key = self._id_convert, self._key_
        callback([_id_convert(res, _key) for res in result_list[0]])

    @tornado.gen.engine
    def get_list(self, query={}, callback=None):
        response_list = []
        conditions = {}
        fields = {}
        sorts = []
        pos = 0
        count = 39999
        if "conditions" in query:
            conditions = query["conditions"]
        if "pos" in query:
            pos = query["pos"]
        if "count" in query:
            count = query["count"]
        if "fields" in query:
            fields = query["fields"]
        if "sorts" in query:
            sorts = query["sorts"]
        if 'conditions' not in query:
            conditions = query
        # add conditon delete_flag is not 1
        conditions[DELETE_FLAG] = {'$ne': '1'}
        if QUERY_COLLECT:
            logging.info("mongoQueryCollect: %s, %s, %s", self._db_, self._table_,
                         simplejson.dumps(conditions, default=convert_to_builtin_type))
        sorts = [[x if x != self._key_ else MONGODB_ID for x in y] for y in sorts]
        if not sorts:
            sorts.append([MONGODB_ID, pymongo.DESCENDING])

        pos = int(pos)
        count = int(count)
        if self._key_ in conditions:
            conditions[MONGODB_ID] = conditions[self._key_]
            del conditions[self._key_]
        if self._key_ in fields:
            fields[MONGODB_ID] = fields[self._key_]
            del fields[self._key_]
        if not fields.keys():
            fields = None
        result_list, error = yield tornado.gen.Task(self.dao.find, spec=conditions,
                                                    fields=fields, limit=count, skip=pos, sort=sorts)
        del conditions[DELETE_FLAG]
        # result_list = result_list[0]
        # for result in result_list:
        #     try:
        #         if MONGODB_ID in result:
        #             result[self._key_] = str(result[MONGODB_ID])
        #             del result[MONGODB_ID]
        #         response_list.append(result)
        #     except Exception, e:
        #         logging.error(e.message)
        #         logging.error("result: %s, self._key_: %s " % (str(result), self._key_))
        # callback(response_list)
        _id_convert, _key = self._id_convert, self._key_
        callback([_id_convert(res, _key) for res in result_list[0]])

    @tornado.gen.engine
    def find_one(self, spec, fields=None, include_del=False, callback=None):
        if self._key_ in spec:
            spec[MONGODB_ID] = spec[self._key_]
            del spec[self._key_]
        # add conditon delete_flag is not 1
        if not include_del:
            spec[DELETE_FLAG] = {'$ne': '1'}
        if QUERY_COLLECT:
            logging.info("mongoQueryCollect: %s, %s, %s", self._db_, self._table_,
                         simplejson.dumps(spec, default=convert_to_builtin_type))
        result_lst = yield tornado.gen.Task(self.do_query, spec, fields, count=1)
        del spec[DELETE_FLAG]
        # model, error = yield tornado.gen.Task(self.dao.find_one, spec, fields=fields)
        # model = model[0]
        # if type(model) == tuple and len(model) > 0:
        #     model = model[0]
        # if type(model) == list and len(model) > 0:
        #     model = model[0]
        # if model:
        #     model[self._key_] = str(model[MONGODB_ID])
        #    del model[MONGODB_ID]
        # callback(model)
        callback(result_lst[0] if result_lst else None)

    @tornado.gen.engine
    def get_by_id(self, key_value, callback=None):
        result = yield tornado.gen.Task(self.find_one, {self._key_: key_value})
        callback(result)

    @tornado.gen.engine
    def count(self, query={}, delete_flag=True, callback=None):
        try:
            if self._key_ in query:
                query[MONGODB_ID] = query[self._key_]
                del query[self._key_]
            # add conditon delete_flag is not 1
            if delete_flag:
                query[DELETE_FLAG] = {'$ne': '1'}
            if QUERY_COLLECT:
                logging.info("mongoQueryCollect: %s, %s, %s", self._db_, self._table_,
                             simplejson.dumps(query, default=convert_to_builtin_type))
            responses, error = yield tornado.gen.Task(self.dao.find, spec=query,
                                                      fields={self._key_: 1}, sort=[[self._key_, 1]])

            del query[DELETE_FLAG]
            callback(len(responses[0]))
        except Exception as e:
            exc_msg = traceback.format_exc()
            logging.error(exc_msg)
            raise ModelException("count error:%s,e:%s" % (str(query), str(e)))

    @tornado.gen.engine
    def insert(self, doc, manipulate=True, safe=True, check_keys=True, callback=None, **kwargs):

        send_time = int(time.time())
        doc["date"] = send_time
        doc["last_modify"] = send_time

        # 如果doc中有数组，并且数组中是dict,则向其中加入date和id
        for (key, value) in doc.iteritems():
            if not type(value) == list:
                continue
            if not len(value):
                continue
            if type(value[0]) == dict:
                # if id not exists, add id, date etc for sub doc
                if "id" not in value:
                    for d in value:
                        d["id"] = self.get_id()
                        d["date"] = send_time
                        d["last_modify"] = send_time
        # for sync_data, when _id exists, do not need to get_id()
        if MONGODB_ID not in doc:
            if self._key_ not in doc:
                key_value = self.get_id()
            else:
                key_value = doc[self._key_]
                del doc[self._key_]
        else:
            key_value = doc[MONGODB_ID]
            if self._key_ in doc:
                del doc[self._key_]
        doc[MONGODB_ID] = key_value
        yield tornado.gen.Task(self.dao.insert, doc, manipulate=manipulate, safe=safe, check_keys=check_keys, **kwargs)

        # sync data
        if self.need_sync:
            self.sync_insert_data(doc)

        if callback:
            callback(key_value)

    @tornado.gen.engine
    def update(self, spec, document, upsert=False, manipulate=False, safe=True, multi=False, callback=None, **kwargs):

        if self._key_ in spec:
            spec[MONGODB_ID] = spec[self._key_]
            del spec[self._key_]
        # add conditon delete_flag is not 1
        spec[DELETE_FLAG] = {'$ne': '1'}
        if QUERY_COLLECT:
            logging.info("mongoQueryCollect: %s, %s, %s", self._db_, self._table_,
                         simplejson.dumps(spec, default=convert_to_builtin_type))
        old_update_data = document.get("$set", None)
        if old_update_data:
            old_update_data["last_modify"] = int(time.time())
            if DELETE_FLAG in old_update_data:
                del spec[DELETE_FLAG]
            document['$set'] = old_update_data

        unset_data = document.get("$unset", None)
        if unset_data and DELETE_FLAG in unset_data:
            del spec[DELETE_FLAG]

        result = yield tornado.gen.Task(self.dao.update, spec, document, upsert=upsert,
                                        manipulate=manipulate, safe=safe, multi=multi, **kwargs)

        if self.need_sync:
            self.sync_update_data(spec, document, upsert, safe)

        if callback:
            callback(result)

    @tornado.gen.engine
    def delete(self, spec, safe=True, callback=None, **kwargs):

        if self._key_ in spec:
            spec[MONGODB_ID] = spec[self._key_]
            del spec[self._key_]

        # add conditon delete_flag is not 1
        spec[DELETE_FLAG] = {'$ne': '1'}
        if QUERY_COLLECT:
            logging.info("mongoQueryCollect: %s, %s, %s", self._db_, self._table_,
                         simplejson.dumps(spec, default=convert_to_builtin_type))
        update_set = {
            '$set': {
                DELETE_FLAG: '1'
            }
        }

        result = yield tornado.gen.Task(self.dao.update, spec, update_set, multi=True)

        if self.need_sync:
            self.sync_delete_data(spec)

        if callback:
            callback(result)

    @tornado.gen.engine
    def find_and_modify(self, spec, document, upsert=False,
                        manipulate=False, safe=True, multi=False, callback=None, **kwargs):

        if self._key_ in spec:
            spec[MONGODB_ID] = spec[self._key_]
            del spec[self._key_]
        # add conditon delete_flag is not 1
        spec[DELETE_FLAG] = {'$ne': '1'}
        if QUERY_COLLECT:
            logging.info("mongoQueryCollect: %s, %s, %s", self._db_, self._table_,
                         simplejson.dumps(spec, default=convert_to_builtin_type))
        old_update_data = document.get("$set", None)
        if old_update_data:
            old_update_data["last_modify"] = int(time.time())
            document['$set'] = old_update_data

        from bson.son import SON

        command = SON(
            [('findAndModify', self._table_), ('query', spec), ('update', document), ('upsert', False), ('new', True)])

        command.update(kwargs)

        result = yield tornado.gen.Task(self.async_client.connection("$cmd", self._db_).find_one, command,
                                        _must_use_master=True, _is_command=True)

        flag = result[0][0]['value']
        if flag and self.need_sync:
            self.sync_update_data(spec, document)

        callback(flag)

    def get_id(self):
        return str(ObjectId())

    def sync_insert_data(self, doc):  # for mongodb $ operator anti-moth 20160226
        if MONGODB_ID in doc and isinstance(doc[MONGODB_ID], ObjectId):
            doc[MONGODB_ID] = str(doc[MONGODB_ID])
        self.sync_class.send_insert(self.module, self.className, doc)

    def sync_update_data(self, spec, doc, upsert=False, safe=False):
        if MONGODB_ID in spec and isinstance(spec[MONGODB_ID], ObjectId):
            spec[MONGODB_ID] = str(spec[MONGODB_ID])
        self.sync_class.send_update(self.module, self.className, spec, doc, upsert, safe)

    def sync_delete_data(self, spec):
        if MONGODB_ID in spec and isinstance(spec[MONGODB_ID], ObjectId):
            spec[MONGODB_ID] = str(spec[MONGODB_ID])
        self.sync_class.send_delete(self.module, self.className, spec)


METHOD_INSERT = "insert"
METHOD_UPDATE = "update"
METHOD_DELETE = "delete"


def convert_to_builtin_type(obj):  # for simplejson dumps user-defined objects. anti-moth 20160226
    # Convert objects to a dictionary of their representation
    class_name = obj.__class__.__name__
    module_name = obj.__module__
    module = __import__(module_name)
    try:
        getattr(module, class_name)
        return {
            '__class__': class_name,
            '__module__': module_name,
            '__data__': cPickle.dumps(obj)
        }
    except AttributeError:
        return obj

