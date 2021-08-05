# -*- coding:utf-8 -*-
"""
des: 
create time: 
version: 
"""

from src.utils.date_time import *
from src.utils.file_cache import Cache
from src.utils.http_impl import HttpsClient


class WxMpTemplateMsg(dict):
    """
    公众号模版消息
    """

    def __init__(self, template_id, url = None, data = {}):
        """

        :param template_id:
        :param url:
        :param data:
        """
        self.template_id    =   template_id
        self.url            =   url
        self.data           =   data
        dict.__init__(self, template_id = template_id, url = url, data = data)


    def add_data(self, key, value, color = "#000000"):
        """

        :param key:
        :param value:
        :param color:
        :return:
        """
        if key in self["data"]:
            raise Exception("data for key %s already exists!" % key)
        self["data"][key] = {
            "value"     :   value,
            "color"     :   color
        }


    def set_data(self, key, value, color = "#000000"):
        """

        :param key:
        :param value:
        :param color:
        :return:
        """
        self["data"][key] = {
            "value"     :   value,
            "color"     :   color
        }


    def set_recv(self, recv_openid):
        """

        :param recv_openid:
        :return:
        """
        self["touser"]  =   recv_openid




class TokenMgr(dict):
    """
    凭据管理器
    """

    __instance = None

    class Token(object):
        """
        token
        """
        def __init__(self, token, expire_time):
            """

            :param token:
            :param expire_time:
            """
            self.token          =   token
            self.expire_time    =   expire_time
            self.create_time    =   unix_timestamp()


        def get_token(self):
            """

            :return:
            """
            #过期了
            if unix_timestamp() - self.create_time > self.expire_time:
                return None
            return self.token


    def __new__(cls, *args, **kwargs):
        """
        单例模式
        :param args:
        :param kwargs:
        """
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance


    def get_token(self, appid, secret_key):
        """

        :param appid:
        :param secret_key:
        :return:
        """
        key = self.__key(appid, secret_key)
        if key not in self:
            #检查缓存
            token = Cache.get(key)
            #从服务器获取
            if token is None:
                token, expire_time = self.__request_for_token(appid, secret_key)
                Cache.put(key, token, expire_time)
                self[key] = TokenMgr.Token(token, expire_time)
            return token
        else:
            token = self[key].get_token()
            #过期了
            if token is None:
                token, expire_time = self.__request_for_token(appid, secret_key)
                Cache.put(key, token, expire_time)
                self[key] = TokenMgr.Token(token, expire_time)
            return token


    def __request_for_token(self, appid, secret_key):
        """

        :param appid:
        :param secret_key:
        :return:
        """
        url = """https://api.weixin.qq.com/cgi-bin/token"""
        result = HttpsClient.get(url, data = {"grant_type":"client_credential", "appid":appid, "secret":secret_key}, json_ret=True)
        return result["access_token"], result["expires_in"]


    def __key(self, appid, secret_key):
        """

        :param appid:
        :param secret_key:
        :return:
        """
        return "wxmp_%s_%s" % (appid, secret_key)



class WxMpClient(object):
    """微信公众号客户端"""

    def __init__(self, appid, secret_key):
        """
        初始化客户端
        :param appid:
        :param secret_key:
        :return:
        """
        self.appid          =   appid
        self.secret_key     =   secret_key
        self.token_mgr      =   TokenMgr()


    def send_template_msg(self, recv_openid, template_msg):
        """
        发送模版消息
        :param recv_openid:
        :param template_msg:
        :return:
        """
        if not isinstance(template_msg, WxMpTemplateMsg):
            raise Exception("param template_msg must be a WxMpTemplateMsg object")
        #获取token
        token = self.token_mgr.get_token(self.appid, self.secret_key)
        url = """https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}""".format(token = token)
        #设置接收人
        template_msg.set_recv(recv_openid)
        #发送消息
        result = HttpsClient.post(url, template_msg, json_ret=True)
        if result.get("errcode") != 0:
            raise Exception("send msg failed, %s" % str(result))




