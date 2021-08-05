# -*- coding:utf-8 -*-
"""
des: 
create time: 2018-7-28
version:
"""
import time
from src.utils.log import Log
import traceback


class Fresher(object):
    """定时刷新器， 用于间隔一段时间从DB或本地数据中取出数据，避免对DB造成太大压力，用于更新不频繁的数据读取"""

    #默认数据刷新时间未300秒
    DEFAULT_FRESH_INTERVAL  =   300

    def __init__(self, interval = DEFAULT_FRESH_INTERVAL):
        """
        初始化
        """
        self.interval            =   interval
        self.last_fresh_time     =   0
        self.is_freshed          =   True
        self.info                = ""
        if self.check_fresh() : self.do_fresh()



    def __set_info(self, info):
        """
        提示日志
        :param info:
        :return:
        """
        Log.debug("load data from db error" + info)


    def __set_error(self, strError):
        """
        错误日志
        :param strError:
        :return:
        """
        self.info = strError
        Log.error(strError)


    def load(self):
        """
        加载数据核心类，需要在子类中继承
        :return:
        """
        raise Exception("function load must be overide in child class")


    def close(self):
        """
        关闭刷新
        :return:
        """
        self.is_freshed = False


    def open(self):
        """
        开启刷新
        :return:
        """
        self.is_freshed = True


    def do_fresh(self):
        """
        执行刷新动作
        :return:
        """
        load_ret = False
        try:
            self.load()
            load_ret = True
        except Exception as ex:
            self.__set_error(traceback.format_exc())
            load_ret = False
        finally:
            self.last_fresh_time = time.time()
        return load_ret



    def check_fresh(self):
        """

        :return:
        """
        if self.is_freshed is False:
            self.__set_info("Fresh function closed!can not fresh data!")
            return False
        if time.time() - self.last_fresh_time <= self.interval:
            return False
        return True



    @staticmethod
    def fresh(func):
        """
        刷新动作
        :return:
        """
        def wrap(*args, **kwargs):
            self = args[0]
            #检查是否需要刷新
            if self.check_fresh() is True and self.do_fresh() is False:
                raise Exception("[%s]fresh data error:%s" % (func.__name__, self.info))
            return func(*args, **kwargs)
        return wrap


    def reset(self):
        """

        :return:
        """
        self.last_fresh_time = 0


######################################使用方法测试例子#################################

class Roles(Fresher, list):
    """定义一个数据容器"""

    def __init__(self):
        Fresher.__init__(self)


    def load(self):
        self.append(time.time())


    @Fresher.fresh
    def get(self):
        if len(self) == 0:
            return None
        else:
            return self[-1]



if __name__ == "__main__":
    r = Roles()
    while True:
        print("*" * 50)
        print("get:", r.get())
        print(r)
