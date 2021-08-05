#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
des: 使用示例
    from src.utils.http_impl import HttpClient
    print HttpClient.get("https://10.120.106.74:8080/api/tdw/ping")
create time: 2019年11月19日
version:
author: jeffwan
function: http公共组件（支持https访问）
Copyright 1998 - 2019 TENCENT Inc. All Rights Reserved
modify:
    <author>        <modify time>       <des>


"""
import json
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import http.client
import base64
import socket
import platform
import requests
import http.client, ssl, urllib.request, urllib.error, urllib.parse, socket


class HTTPSConnection(http.client.HTTPSConnection):
    """
    https连接兼容
    """
    def __init__(self, *args, **kwargs):
        """
        初始化
        :param args:
        :param kwargs:
        """
        http.client.HTTPSConnection.__init__(self, *args, **kwargs)

    def connect(self):
        """
        连接server
        :return:
        """
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        is_protocol_load = False
        for item_protocol in ("PROTOCOL_TLSv1", "PROTOCOL_SSLv2", "PROTOCOL_TLS", "PROTOCOL_SSLv23", "PROTOCOL_TLSv1_1", "PROTOCOL_TLSv1_2"):
            try:
                self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=getattr(ssl, item_protocol))
                is_protocol_load = True
                break
            except AttributeError:
                pass
        if is_protocol_load is False:
            raise Exception("can not load ssl protocol")


class HTTPSHandler(urllib.request.HTTPSHandler):
    """
    https 连接处理
    """
    def https_open(self, req):
        """
        打开连接
        :param req:
        :return:
        """
        return self.do_open(HTTPSConnection, req)


class __HttpClient(object):
    """
    http 客户端
    """

    @staticmethod
    def get(url, data = {}, headers = None, timeout = 30, json_ret = False, content_type = "application/json"):
        """

        :param url:
        :param data:传递的参数，字符串格式
        :param headers:
        :param content_type:
        :return:
        """
        ##发送请求
        headers = {} if headers is None else headers
        if "Content-Type" not in headers:headers["Content-Type"] = content_type
        params = "&".join("%s=%s" % (key, value)  for key, value in list(data.items()))
        request = urllib.request.Request("%s?%s" % (url, params), None, {} if headers is None else headers)
        req = urllib.request.urlopen(request, None, timeout)
        result = req.read()
        if json_ret is True:
            try:
                result = json.loads(result)
            except Exception as ex:
                raise Exception("result data can not be json loads, msg:%s" % result)
        return result


    @staticmethod
    def post(url, data, headers = None, timeout = 30, json_ret = False, content_type = "application/json", url_encode = False):
        """

        :param url:
        :param data:可json.dumps对象，如字典、列表等
        :param headers:
        :param timeout:
        :return:
        """
        ##发送请求
        json_data = json.dumps(data) if url_encode is False else urllib.parse.urlencode(data)
        headers = {} if headers is None else headers
        if "Content-Type" not in headers:headers["Content-Type"] = content_type
        request = urllib.request.Request(url, bytes(json_data, encoding="utf8"), {} if headers is None else headers)
        req = urllib.request.urlopen(request, None, timeout)
        result = req.read()
        if json_ret is True:
            try:
                result = json.loads(result)
            except Exception as ex:
                raise Exception("result data can not be json loads, msg:%s" % result)
        return result



class __HttpsClient(__HttpClient):
    """https客户端"""

    def __init__(self):
        """
        初始化
        """
        urllib.request.install_opener(urllib.request.build_opener(HTTPSHandler()))



#使用时请导入HttpClient
HttpClient = __HttpClient()
#https专用
HttpsClient = __HttpsClient()

if __name__ == '__main__':
    print(HttpClient.get("http://mf.oa.com/"))