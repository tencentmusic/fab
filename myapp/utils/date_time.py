#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Project: flow_detect
File：   date_time
Description： 
Date：   2017/3/2 21:35
Author： Jeffwan
Copyright 1998 - 2017 TENCENT Inc. All Rights Reserved
modify：
    Jeffwan        2017/3/2       Create
"""
import time
import math
import threading

date_lock = threading.RLock()

def datetime(format ="%Y-%m-%d %H:%M:%S", unixtime = None):
    """
    获取当前时间
    :param format:时间格式化
    :param unixtime:
    :return:"%Y-%m-%d %H:%M:%S"形式的字符串
    """
    with date_lock:
        unixtime = time.time() if unixtime is None else unixtime
        return time.strftime(format, time.localtime(unixtime))


def datadesc(mode ="day", offset = 1, format=None):
    """
    生成昨日的数据日期
    :return:
    """
    with date_lock:
        if mode == "day":
            format = "%Y%m%d" if format is None else format
            return datetime(format=format, unixtime=unix_timestamp() - 24 * 3600 * offset)
        if mode == "hour":
            format = "%Y%m%d%H" if format is None else format
            return datetime(format=format, unixtime=unix_timestamp() - 3600 * offset)


def get_readable_time(unixtime):
    """

    :param unixtime:
    :return:
    """
    unixtime = int(unixtime)
    if unixtime < 60:
        return "%ss" % unixtime
    if unixtime >= 60 and unixtime < 3600:
        min = math.floor(unixtime / 60)
        sec = unixtime % 60
        return "%sm%ss" % (min, sec)
    if unixtime >= 3600 and unixtime < 3600 * 24:
        hour = math.floor(unixtime / 3600)
        unixtime = unixtime % 3600
        min = math.floor(unixtime / 60)
        sec = unixtime % 60
        return "%sh%sm%ss" % (hour, min, sec)
    if unixtime >= 3600 * 24:
        day  = math.floor(unixtime / (3600 * 24))
        unixtime = unixtime % (3600 * 24)
        hour = math.floor(unixtime / 3600)
        unixtime = unixtime % 3600
        unixtime = unixtime % 60
        min = math.floor(unixtime / 60)
        sec = unixtime % 60
        return "%sd%sh%sm%ss" % (day, hour, min, sec)


def unix_timestamp():
    """
    获取当前的整型unix时间戳
    :return:
    """
    return int(time.time())



def datetime_convert(date_time, format ="%Y-%m-%d %H:%M:%S", target_format ="%Y-%m-%d %H:%M:%S"):
    """
    时间格式转换
    :param datetime:
    :param format:
    :param target_format:
    :return:
    """
    with date_lock:
        unixtime = time.mktime(time.strptime(date_time, format))
        return datetime(format= target_format, unixtime= unixtime)


def date2unix(datetime, format ='%Y-%m-%d %H:%M:%S'):
    """
    将指定格式的日期转为时间戳形式
    :param datetime:
    :param format:
    :return:
    """
    return int(time.mktime(time.strptime(datetime, format)))


def datetime2unix(datetime):
    """
    datetime类型的数据转为时间戳
    :param datetime:
    :return:
    """
    return int(time.mktime(datetime.timetuple()))