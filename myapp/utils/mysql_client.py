#!/usr/bin/env python
# -*-coding:UTF-8-*-#

import pymysql
import threading
from .log import Log

_MAX_RECONNECT_NUM = 3
#MYSQL 默认端口
_DB_DEFAULT_PORT = 3306

class MysqlClient(object):
    """
    用于访问数据库的客户端
    """
    DB_HOST     = None
    DB_USER     = None
    DB_PASSWD   = None
    DB_DATABASE = None
    DB_CHARSET  = "utf8"
    DB_PORT     = _DB_DEFAULT_PORT
    
    def __init__(self, host, user, passwd, db_name, charset='utf8', port = _DB_DEFAULT_PORT):
        """
        初始化
        :param host:
        :param user:
        :param passwd:
        :param db_name:
        :param charset:
        :param port:
        """
        self.__host      = host
        self.__user      = user
        self.__password  = passwd
        self.__database  = db_name
        self.__port      = port
        self.__charset   = charset
        self.__connection = None
        self.__cursor = None
        self.__lock = threading.Lock()
        self.__is_reconnect = 0
        self.__load_file = 1

    def __del__(self):
        """
        销毁数据库连接
        :return:
        """
        self.destroy()

    
    def GetLastError(self):
        return self.__strLastError


    def destroy(self):
        """
        销毁数据库连接
        :return:
        """
        try:
            if self.__cursor is not None:
                self.__cursor.close()
        except:
            pass
        try:
            if self.__connection is not None:
                self.__connection.close()
        except:
            pass
        self.__connection = None
        self.__cursor = None


    def reconnect(self):
        """
        如果这个对象在多个线程中使用，建议不要使用此方法
        适合在单线程中使用
        """
        self.destroy()
        return self.__connect_db()

    
    def check_connected(self):
        """
        检查数据库是否已连接
        :return:
        """
        if self.__connection is None:
            return False
        ret = True
        try:
            self.__connection.ping()
        except:
            ret = False
        return ret


    def __is_connected(self):
        """

        :return:
        """
        if (self.__strLastError.find("Can't connect to") != -1 and \
            self.__strLastError.find("MySQL server through socket") != -1) or\
            self.__strLastError.find("MySQL server has gone away") != -1: 
            return False
        return True

    
    def __connect_db(self):
        """

        :return:
        """
        ret = True
        try:
            load_file = 1
            if self.__load_file ==0:
                load_file = 0

            self.__connection = pymysql.connect(host = self.__host,
                                                user = self.__user,
                                                passwd = self.__password,
                                                db = self.__database,
                                                port = self.__port,
                                                charset = self.__charset,
                                                local_infile= load_file)

            self.__cursor = self.__connection.cursor()
            self.__strLastError = ""
            self.__is_reconnect = 0
        except Exception as ex:
            self.__is_reconnect += 1
            self.destroy()
            ret = False
            raise Exception("connect db[%s] failed." % self.__host + str(ex))
        return ret


    def __connect(self):
        """

        :return:
        """
        self.__lock.acquire()
        while self.__is_reconnect < _MAX_RECONNECT_NUM:
            #先检查，多线程防止重复登录
            if self.check_connected():
                break
            #也许已经连接过,连接线需要销毁之前连接对象
            self.destroy()
            if self.__connect_db():
                ret = True
                break
        self.__lock.release()


    def __connect_v1_0(self):
        """

        :return:
        """
        ret = True
        if self.__connection is not None and self.__is_connected():
            self.__strLastError = ""
            self.__is_reconnect = 0
            return ret
        
        #连接断开，重连前，清理资源
        if self.__connection is not None:
            self.destroy()

        self.__lock.acquire()
        #多线程防止重复登录
        if self.__connection is not None and self.__is_connected():
            self.__lock.release()
            self.__strLastError = ""
            self.__is_reconnect = 0
            return True

        if self.__is_reconnect >= _MAX_RECONNECT_NUM:
            self.__lock.release()
            return False

        #连接数据库
        ret = self.__connect_db()
        self.__lock.release()
        
        return ret


    def escape(self, field):
        """
        转义
        :param field:
        :return:
        """
        return pymysql.escape_string(field)


    def execute(self, sql, params = None):
        """
        功能：sql 执行
        参数：strSql，sql语句  
        tupleParam，sql中%s的值（注意sql中%s替换需要代替的数字，字符串且字段值时字符串不需要单引号）
        返回值： True 执行sql成功   False 执行sql失败
        """
        self.__connect()
        if params is None:
            self.__cursor.execute(sql)
        else:
            self.__cursor.execute(sql, params)
        self.__connection.commit()

    
    def insert(self, sql, params = None):
        """
        功能：单行sql执行，用于获取当前插入sql的自增id（`f_id` int unsigned NOT NULL AUTO_INCREMENT）值
        参数：strSql，sql语句  
        tupleParam，sql中%s的值（注意sql中%s替换需要代替的数字，字符串且字段值时字符串不需要单引号）
        返回值： 自增id值   -1 执行sql失败
        """
        self.__connect()
        if params is None:
            self.__cursor.execute(sql)
        else:
            self.__cursor.execute(sql, params)
        self.__connection.commit()
        return int(self.__cursor.lastrowid)

    
    def execute_many(self, sql, params):
        """
        功能：执行多行sql
        参数：strSql，sql语句  
        tupleParam，sql中%s的值（注意sql中%s替换需要代替的数字，字符串且字段值时字符串不需要单引号）
        返回值： True 执行sql成功   False 执行sql失败
        """
        self.__connect()
        self.__cursor.executemany(sql, params)
        self.__connection.commit()


    def select(self, sql, params = None):
        """
        功能：查询sql语句执行，获取select结果
        参数：strSql，sql语句  
        tupleParam，sql中%s的值（注意sql中%s替换需要代替的数字，字符串且字段值时字符串不需要单引号）
        返回值： bool，list   True SQL执行成功， list为多行多字段列表
        """
        self.__connect()
        if params is None:
            self.__cursor.execute(sql)
        else:
            self.__cursor.execute(sql, params)
        self.__connection.commit()
        return self.__cursor.fetchall()
