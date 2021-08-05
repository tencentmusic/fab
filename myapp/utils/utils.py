# encoding: utf-8
# test_module exceptions
# by generator 1.138
"""
mf monitor server src.utils file by jeffwan
"""

import re
import gc, os
import traceback
import json
import hashlib
import socket, struct
from datetime import datetime
from uuid import uuid1
from decimal import Decimal
import copy


def uuid():
    return str(uuid1())


class cached_property(object):
    """
    实例属性缓存，配合Storage使用味道更加
    """
    def __init__(self, func):
        """
        初始化
        :param func: @property装饰的函数
        """
        self.func = func


    def __get__(self, obj, cls):
        """

        :param obj:
        :param cls:
        :return:
        """
        if obj is None:
           return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value



class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.
        定义一个容器，可以使用obj.foo的方式来访问其间的数据，实际继承自字典dict
        >>> o = storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'

    """

    def __init__(self, **kwargs):
        """

        :param kwargs:
        """
        dict.__init__(self, **kwargs)


    def __getattr__(self, key):
        """

        :param key:
        :return:
        """
        return self[key]


    def __setattr__(self, key, value):
        """

        :param key:
        :param value:
        :return:
        """
        self[key] = value


    def __delattr__(self, key):
        """

        :param key:
        :return:
        """
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)


    def __repr__(self):
        """

        :return:
        """
        return '<Storage ' + dict.__repr__(self) + '>'

#大小写兼容
storage = Storage

def get_file_lines(filename):
    """

    :param filename:
    :return:
    """
    if os.path.exists(filename) is False:
        return 0
    return len(["" for line in open(filename, "r")])


def md5(data):
    """
    对一个字符串求md5值
    :_Param strData:要求md5值的字符串
    :return:md5字符串
    """
    # 必须重新实例化
    md5_instance = hashlib.md5()
    md5_instance.update(bytes(data, encoding="utf8"))
    return md5_instance.hexdigest()


class Type():
    """定义常用数据类型"""
    DICT    = [dict]
    STR     = [str]
    INT     = [int]
    LONG    = [int]
    DOUBLE  = [float]
    COMPLEX = [complex]
    LIST    = [list]
    UNICODE = [str]
    TUPLE   = [tuple]
    BOOL    = [bool]
    SET     = [set]
    #自定义类型
    NUM     = [int, int, float, complex]
    INT_NUM = [int, int]
    #与STR的区别是允许unicode或者string类型的数据
    STRING  = [str, str]


class Param(object):
    """
    单个参数校验
    Param(strVariable, Type.INT, [strParamName = None, bNotNone = True, bNotEmpty = False, iMaxLen = 20, tplSpan = (0, 255)]).verify()
    """

    KEY_CONDITION = "condition"
    KEY_ACTION    = "action"

    def __init__(self, value, type, param_type = None, not_none = False, not_empty = False, max_len = -1, span = ()):
        """
        初始化一个配置项目
        :_Param strVarValue     : 变量值
        :_Param constType       : 变量类型, 从类Type中取
        :_Param bNone           : 是否可以为None
        :_Param bEmpty          : 是否可以为空，主要用于list或者dict或者tuple等集合类型
        :_Param iMaxLen         : 最大长度，默认-1为不检测
        :_Param tplSpan         : 取值范围
        :param param_type     : 变量名称
        """

        if type not in [Type.DICT, Type.STR, Type.INT, Type.LONG, Type.DOUBLE,
                        Type.COMPLEX, Type.LIST, Type.UNICODE, Type.TUPLE, Type.STRING,
                        Type.BOOL, Type.SET, Type.NUM, Type.INT_NUM]:

            raise TypeError("type <%s> not in defined." % (type))

        #取出数据
        self.value = value
        self.type   = type
        self.not_none    = not_none
        self.not_empty   = not_empty
        self.max_len     = max_len
        self.span     = span
        self.param_name  = param_type if param_type else "unkown_variable"
        assert isinstance(self, Param) is True


    def verify(self):
        """
        参数校验
        :return:True/False
        """
        methods = [
                           {   # 检查项触发的条件
                               Param.KEY_CONDITION     : self.not_none is True,
                               # 具体执行的函数
                               Param.KEY_ACTION        : self._check_none
                           },{
                               Param.KEY_CONDITION     : True,
                               Param.KEY_ACTION        : self._check_type
                           },
                           {
                               Param.KEY_CONDITION     : self.not_empty is True,
                               Param.KEY_ACTION        : self._check_empty
                           },
                           {
                               Param.KEY_CONDITION     : self.max_len != -1,
                               Param.KEY_ACTION        : self._check_max
                           },
                           {
                               Param.KEY_CONDITION     : len(self.span),
                               Param.KEY_ACTION        : self._check_span
                           }]

        #调用检查项
        for action in methods:
            #判断是否满足条件
            if action[Param.KEY_CONDITION]:
                #调用函数
                action[Param.KEY_ACTION]()

        return True



    def _check_type(self):
        """
        类型校验
        :return:
        """
        if self.value is None and self.not_none is False:
            return True
        param_type = type(self.value)
        # 校验数据类型
        ret = False
        for item_param_type in self.type:
            if ret:
                break
            if isinstance(self.value, item_param_type):
                ret = True
        if not ret:
            raise TypeError("Param <%s> must be %s type, not %s." % (self.param_name, str(self.type), param_type))


    def _check_none(self):
        """
        检查是否为None
        :return:
        """
        # 校验是否为None
        if self.not_none is True and self.value is None:
            raise Exception("Param <%s> can not be None but None." % self.param_name)


    def _check_item_empty(self, value, type):
        """
        是否是容器类型
        :param value:
        :param type:
        :return:
        """
        if self.value is None and self.not_none is False:
            return True
        if isinstance(value, type):
            return True
        return False


    def _check_empty(self):
        """
        检查是否为空
        :return:
        """
        # 校验是否为空
        if True not in [self._check_item_empty(self.value, x) for x in [str, str, dict, list, set, tuple]]:
            return

        if self.not_empty is True and len(self.value) == 0:
            raise Exception("Param <%s> can not be empty but empty." % self.param_name)



    def _check_max(self):
        """
        校验最大长度
        :return:
        """
        #校验最大长度
        if True in [self._check_item_empty(self.value, x) for x in [str, str, dict, list, set, tuple]]\
            and self.max_len != -1 and len(self.value) > self.max_len:
            raise Exception("Param <%s> can not be longer than %s." % (self.param_name, self.max_len))

        if True in [self._check_item_empty(self.value, x) for x in [int, float, int]]\
            and self.max_len != -1 and self.value > self.max_len:
            raise Exception("Param <%s> can not be longer than %s." % (self.param_name, self.max_len))



    def _check_span(self):
        """
        取值范围检查
        :return:
        """
        # 取值范围校验
        iLen = len(self.span)

        # 上下阈参数校验
        if iLen > 0 and iLen != 2:
            raise Exception("Param <%s>:span config must have 2 limit numbers." % (self.param_name))

        if True not in [self._check_item_empty(self.value, x) for x in [int, int, float]]:
            return

        # 取上下阈值
        min, max = self.span
        if self.value < min or self.value > max:
            raise Exception("Param <%s> out of range(%s, %s)" % (self.param_name, min, max))


def to_string(obj, encoding ="utf8"):
    """
    将字典或者数据中的bytes转化为中文
    :param obj:
    :param encoding:
    :return:
    """
    #字符串类型
    if isinstance(obj, str) or isinstance(obj, bytes):
        return String(obj, charset=encoding)
    #不可转换对象，直接返回
    if not isinstance(obj, list) and not isinstance(obj, dict) and not isinstance(obj, tuple) and not isinstance(obj, set):
        return obj
    #复合数据类型
    if isinstance(obj, list):
        for index in range(0, len(obj)):
            if isinstance(obj[index], str) or isinstance(obj[index], bytes):
                obj[index] = String(obj[index], charset = encoding)
            else:
                obj[index] = to_string(obj[index], encoding = encoding)
        return obj
    elif isinstance(obj, dict):
        for key in obj:
            if isinstance(obj[key], str) or isinstance(obj[key], bytes):
                obj[key] = String(obj[key], charset=encoding)
            else:
                obj[key] = to_string(obj[key], encoding=encoding)
        return obj
    elif isinstance(obj, tuple):
        new_list = []
        for item in obj:
            if isinstance(item, str) or isinstance(item, bytes):
                new_list.append(String(item, charset=encoding))
            else:
                new_list.append(to_string(item, encoding=encoding))
        return tuple(new_list)
    elif isinstance(obj, set):
        new_list = []
        for item in obj:
            if isinstance(item, str) or isinstance(item, bytes):
                new_list.append(String(item, charset=encoding))
            else:
                new_list.append(to_string(item, encoding=encoding))
        return set(new_list)
    return obj


def make_round(num, dot_bit):
    """

    :param num:
    :param dot_bit:
    :return:
    """
    if dot_bit > 0:
        return str(round(num, dot_bit))
    else:
        str_num = "%f" % num
        if str_num.find(".") != -1:
            return str_num.split(".")[0]
        return str_num


def is_number(text):
    """

    :param text:
    :return:
    """
    if not isinstance(text, str):
        raise Exception("function is_number only support text param, not %s" % type(text))
    if text.isdigit():
        return True
    split_text = text.strip("-").split(".")
    if len(split_text) == 2 and split_text[0].isdigit() and split_text[1].isdigit():
        return True
    return False


def number_readable(num, dot_bit, min = 1000):
    """
    将数字转换为可读单位
    :param num:
    :return:
    """
    def in_range(num, range_start, range_end):
        """

        :param num:
        :param range_start:
        :param range_end:
        :return:
        """
        if num >= range_start and num < range_end:
            return True
        return False
    if not is_number(str(num)):
        raise Exception("param num must be a number, value:[%s]" % num)
    num = float(num)
    if num <= min:
        return make_round(num, dot_bit)
    if in_range(num, 10000, 100000000):
        return "%s万" % make_round(num / 10000, dot_bit)
    elif in_range(num, 100000000, 1000000000000):
        return "%s亿" % make_round(num / 100000000, dot_bit)
    elif num > 1000000000000:
        return "%s万亿" % make_round(num / 1000000000000, dot_bit)
    else:
        return make_round(num, dot_bit)


class Params(object):
    """
    批量校验参数， Param是单个参数校验
    Params([Param(strValue, Type.NUM, 'age'), Param(strValue2, Type.STR, 'age')]).verify()
    """

    def __init__(self, lstParams):
        """
        初始化
        :param lstParams: 参数list，每一个元素为一个Param对象
        """
        self.lstParams = lstParams


    def verify(self):
        """
        参数校验
        :return:
        """
        list(map(lambda x: self._checkParam(x), self.lstParams))
        return True



    def _checkParam(self, objParam):
        """
        参数校验
        :param objParam:
        :return:
        """
        if not isinstance(objParam, Param):
            raise Exception("item Param must be Param type!")

        objParam.verify()


def sys_gc(object):
    """
    回收一个对象
    :param object:
    :return:
    """
    del object
    gc.collect()


class __String():
    """任意类型字符串或者unicode转成string类型，默认编码utf8"""
    def __call__(self, text, charset ='utf8', force = False):
        """

        :param text:
        :param charset:
        :param force:
        :return:
        """
        if not isinstance(text, bytes) and not isinstance(text, str):
            text = str(text)
        is_bytes = isinstance(text, bytes)
        if is_bytes:
            return text.decode(charset)
        else:
            return text

String = __String()


def get_local_ip():
    """
    funciton name:__getPort
    des:获获取本机 eth0 ip地址
    input:None
    output:strIp
    """
    try:
        obj_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        obj_socket.connect(('192.168.0.0', 80))
        ip = obj_socket.getsockname()[0]
    finally:
        obj_socket.close()
    return ip

def get_int(int_num, default = -1):
    """安全转换为整型"""
    try:
        return int(int_num)
    except Exception:
        return default


def get_str(string, default ="Blank Str!"):
    """安全转换为整型"""
    try:
        return str(string)
    except Exception:
        return default



