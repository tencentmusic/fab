# -*- coding:utf-8 -*-
"""
des: 
create time: 
version: 
"""

from src.utils.java4py import Java4py
from src.utils.config import Config

import jpype
import jpype.imports
from jpype.types import *


class TdwAuthClient(object):
    """
    tdw的鉴权接口，通过调用tdw的java api实现
    doc：http://tdwsecureguide.pages.oa.com/
    底层请求的域名是：auth.tdw.oa.com
    dev环境请添加hosts并开通网络策略

    """

    @staticmethod
    def gen_signature(username, cmk, service, url = None):
        """
        生成客户端签名
        :param username:
        :param cmk:
        :param service:
        :param url:
        :return:
        """
        jar = "{tools}/tdw_auth_client/tdw_auth_client.jar".format(
            tools = Config.tools_dir.rstrip("/")
        )
        with Java4py(jars=jar) as java:
            TdwAuthClientClass = JClass("TdwAuthClient")
            if url is not None:
                TdwAuthClientClass.setServiceUrl(url)
            return TdwAuthClientClass.genClientAuthentication(username, cmk, service)


