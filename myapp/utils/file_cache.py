# -*- coding:utf-8 -*-
"""
File： C:/Users/Administrator/eclipse_workspace/monitor_platform/test/flow_detect/src/src.utils/file_cache.py
Description： 文件缓存
Date：  2016年4月14日
Author：Jeffwan
Copyright 1998 - 2016 TENCENT Inc. All Rights Reserved
modify：
    Jeffwan        2016年4月14日       Create
"""

import os
import time
import json
import hashlib
import traceback
from datetime import datetime
from decimal import Decimal
from .log import Log
from src.utils.config import Config
from multiprocessing import Lock
from src.utils.utils import md5



class Cache(object):
    cache = None

    @staticmethod
    def get(key):
        """

        :param key:
        :return:
        """
        if Cache.cache is None:
            Cache.cache = _Cache()
        return Cache.cache.get(key)


    @staticmethod
    def put(key, value, retire = 3600):
        """

        :param self:
        :param key:
        :param value:
        :param retire:
        :return:
        """
        if Cache.cache is None:
            Cache.cache = _Cache()
        return Cache.cache.put(key, value, retire)


    @staticmethod
    def rm(key):
        """

        :param strKey:
        :return:
        """
        if Cache.cache is None:
            Cache.cache = _Cache()
        return Cache.cache.rm(key)


class _Cache():

    def __init__(self):
        """

        :param strCacheFolder:
        """
        cache_dir = Config.cache_dir
        self.err_msg = ""
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)
        self.cache_dir = cache_dir
        self.lock = Lock()

    
    def __get_md5_key(self, key):
        """
        Function name:__getMd5
        Description:生成key的md5
        Date:2016年4月14日
        Author:Jeffwan
        Input:key
        OutPut:md5Key
        """
        return md5(key)


    def put(self, key, value, retire = 3600):
        """
        Function name:put
        Description:放入缓存
        Date:2016年4月14日
        Author:Jeffwan
        Input:strKeyName, strValue
        OutPut:True/False
        """
        self.lock.acquire()
        ret = False
        try:
            if self.cache_dir.endswith("/") is False:
                self.cache_dir += "/"
            filename = "%s%s.cache" % (self.cache_dir, self.__get_md5_key(key))

            data = {
                "data": value,
                "retire": retire,
                "create_time": time.time(),
                "retire_time": time.time() + retire
            }

            # 写入文件
            with open(filename, "w") as file:
                file.write(json.dumps(data))
            ret = True
        except Exception as ex:
            Log.error("[%s]set cache failed:%s" % (key, traceback.format_exc()))
            ret = False
        self.lock.release()
        return ret


    def get(self, key):
        """
        Function name:put
        Description:放入缓存
        Date:2016年4月14日
        Author:Jeffwan
        Input:strKeyName, strValue
        OutPut:True/False
        """
        self.lock.acquire()
        result = self.__get(key)
        self.lock.release()
        return result


    def __get(self, key):
        """

        :param strKey:
        :return:
        """
        try:
            if self.cache_dir.endswith("/") is False:
                self.cache_dir += "/"
            filename = "%s%s.cache" % (self.cache_dir, self.__get_md5_key(key))
            if os.path.exists(filename) is False:
                return None
            # 读取文件
            data = ""
            with open(filename, "r") as file:
                data = file.read()
            if not data.strip():
                return None
            dict_data = json.loads(data)
            # 判断是否过期
            value = dict_data["data"]
            retire_time = dict_data["retire_time"]
            if time.time() > retire_time and os.path.exists(filename):
                os.remove(filename)
                return None
            # 未过期 返回存储的值
            return value
        except Exception as ex:
            Log.error("[%s]read from cache failed:%s" % (key, traceback.format_exc()))
            return None


    def rm(self, key):
        """
        Function name:put
        Description:清理缓存
        Date:2016年4月14日
        Author:Jeffwan
        Input:strKeyName, strValue
        OutPut:True/False
        """
        ret = False
        self.lock.acquire()
        try:
            if self.cache_dir.endswith("/") is False:
                self.cache_dir += "/"
            filename = "%s%s.cache" % (self.cache_dir, self.__get_md5_key(key))
            if os.path.exists(filename) is True:
                os.remove(filename)
            ret = True
        except Exception as ex:
            Log.error("[%s]rm cache failed:%s" % (key, traceback.format_exc()))
            ret = False
        self.lock.release()
        return ret
